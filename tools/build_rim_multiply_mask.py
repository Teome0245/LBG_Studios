import json
import struct
import numpy as np
from PIL import Image, ImageDraw, ImageFilter

# 1. Charger Compagnon.vrm pour extraire la géométrie exacte du tronc
vrm_path = 'packages/compagnon-desktop/overlay/vrm/Compagnon.vrm'
with open(vrm_path, 'rb') as f:
    f.read(12)
    chunk_len, _ = struct.unpack('<II', f.read(8))
    gltf = json.loads(f.read(chunk_len).decode('utf-8'))
    bin_chunk_len, _ = struct.unpack('<II', f.read(8))
    bin_data = f.read(bin_chunk_len)

vrm_ext = gltf['extensions']['VRMC_vrm']
humanoid = vrm_ext['humanoid']['humanBones']
node_to_bone = {bone_info['node']: bone_name for bone_name, bone_info in humanoid.items()}

def read_accessor(acc_id):
    acc = gltf['accessors'][acc_id]
    buff_view = gltf['bufferViews'][acc['bufferView']]
    offset = buff_view.get('byteOffset', 0) + acc.get('byteOffset', 0)
    count = acc['count']
    comp_type = acc['componentType']
    type_ = acc['type']
    type_map = {'SCALAR': 1, 'VEC2': 2, 'VEC3': 3, 'VEC4': 4}
    comp_len = type_map[type_]
    if comp_type == 5126:
        fmt = f"<{count * comp_len}f"
    elif comp_type == 5123:
        fmt = f"<{count * comp_len}H"
    elif comp_type == 5121:
        fmt = f"<{count * comp_len}B"
    elif comp_type == 5125:
        fmt = f"<{count * comp_len}I"
    data = struct.unpack_from(fmt, bin_data, offset)
    return np.array(data).reshape((count, comp_len))

prim0 = gltf['meshes'][1]['primitives'][0]
indices = read_accessor(prim0['indices']).flatten().astype(int)
uvs = read_accessor(prim0['attributes']['TEXCOORD_0'])
joints = read_accessor(prim0['attributes']['JOINTS_0']).astype(int)
weights = read_accessor(prim0['attributes']['WEIGHTS_0'])

skin_id = next(n['skin'] for n in gltf['nodes'] if n.get('mesh') == 1 and 'skin' in n)
skin_joints = gltf['skins'][skin_id]['joints']
joint_names = [node_to_bone.get(node_id, f"node_{node_id}") for node_id in skin_joints]

# Identifier les bones dominants de chaque sommet
vertex_bone = []
for i in range(len(uvs)):
    max_w_idx = np.argmax(weights[i])
    dominant_joint_idx = joints[i][max_w_idx]
    bone_name = joint_names[dominant_joint_idx].lower()
    vertex_bone.append(bone_name)

# Rasteriser les triangles purs du tronc en 2048x2048
mask_geo = Image.new('L', (2048, 2048), 0)
draw_geo = ImageDraw.Draw(mask_geo)

num_triangles = len(indices) // 3
for t in range(num_triangles):
    i0, i1, i2 = indices[t*3], indices[t*3+1], indices[t*3+2]
    b0, b1, b2 = vertex_bone[i0], vertex_bone[i1], vertex_bone[i2]
    
    # Doit être un triangle du tronc (spine, chest, hips, neck) sans aucun sommet de membre
    is_trunk = any(k in b0 or k in b1 or k in b2 for k in ['hip', 'spine', 'chest', 'neck'])
    is_limb = any(k in b0 or k in b1 or k in b2 for k in ['arm', 'hand', 'thumb', 'index', 'middle', 'ring', 'little', 'leg', 'foot', 'toe', 'shoulder'])
    
    if is_trunk and not is_limb:
        poly = [
            (float(uvs[i0][0] * 2048), float(uvs[i0][1] * 2048)),
            (float(uvs[i1][0] * 2048), float(uvs[i1][1] * 2048)),
            (float(uvs[i2][0] * 2048), float(uvs[i2][1] * 2048)),
        ]
        draw_geo.polygon(poly, fill=255)

# 2. Charger la texture 2D du corps
skin = Image.open('packages/compagnon-desktop/overlay/vrm/body_skin_android.png').convert('RGB')
skin_arr = np.array(skin)
r = skin_arr[:, :, 0]
g = skin_arr[:, :, 1]
b = skin_arr[:, :, 2]
geo_arr = np.array(mask_geo)

# 3. Filtrer pour ne garder que les plaques
# - Sur la géométrie du tronc uniquement (exclut 100% des bras, jambes, mains, pieds)
# - Teinte bleu titane / gris mecha des plaques : b >= 70 et g >= 45
# - Exclure les néons cyan ultra-lumineux : (g > 185 and b > 200 and r < 100)
# - Exclure la combinaison noire / tissu : b < 70
# - Exclure les ongles ou roses
is_cyan_neon = (g > 185) & (b > 200) & (r < 110)
is_plate_color = (b >= 70) & (g >= 45) & (~is_cyan_neon)
is_plate = (geo_arr > 0) & is_plate_color

# Créer le masque 8-bit noir et blanc (0 = mat, 255 = chrome/métal)
mask_plates = np.zeros((2048, 2048), dtype=np.uint8)
mask_plates[is_plate] = 255

# Nettoyer et adoucir légèrement les bords (anti-aliasing)
plate_img = Image.fromarray(mask_plates, mode='L')
# Léger flou gaussien de rayon 1.0 puis rehaussement pour un bord lissé doux
blurred = plate_img.filter(ImageFilter.GaussianBlur(radius=1.2))
blurred_arr = np.array(blurred)

# Ne jamais déborder de la géométrie du tronc
final_arr = np.where(geo_arr > 0, blurred_arr, 0).astype(np.uint8)
final_mask = Image.fromarray(final_arr, mode='L')

# Sauvegarder dans compagnon-desktop, cortex compagnon_ui et tools
out_desktop = 'packages/compagnon-desktop/overlay/vrm/rim_multiply_mask.png'
out_cortex = 'packages/cortex/compagnon_ui/public/vrm/rim_multiply_mask.png'
final_mask.save(out_desktop)
final_mask.save(out_cortex)
final_mask.save('tools/rim_multiply_mask_preview.png')

print(f"Mask saved! Non-zero pixels: {np.count_nonzero(final_arr)} / {2048*2048}")
print(f"Percentage of UV covered by metallic plates: {100.0 * np.count_nonzero(final_arr) / (2048*2048):.2f}%")
