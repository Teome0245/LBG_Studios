import numpy as np
from PIL import Image, ImageFilter

def join_thigh_plates():
    print("=== 1. Chargement de la texture actuelle ===")
    img = Image.open('packages/compagnon-desktop/overlay/vrm/body_skin_android.png').convert('RGBA')
    arr = np.array(img, dtype=np.float32)

    green_im = Image.open('/home/lbg/.gemini/antigravity-ide/brain/1165e65b-2952-49ad-8ee9-8135d868d941/.user_uploaded/media_1792615525290.png')
    green_arr = np.array(green_im)
    is_uv_mesh = (green_arr[:, :, 1] > 50) & (green_arr[:, :, 0] < 50) & (green_arr[:, :, 2] < 50)

    h, w = 1024, 1024
    y_idx, x_idx = np.ogrid[:h, :w]

    # Extraction des masques de plaques et de néons
    r, g, b = arr[:,:,0], arr[:,:,1], arr[:,:,2]
    is_neon = (g > 200) & (b > 180) & (r < 50)
    is_plate = (b > 140) & (g > 100) & (r < 185) & (~is_neon)
    is_rivet = (r < 40) & (g < 40) & (b < 60)

    print("=== 2. Comblement et lissage du pont entre les deux plaques (Y=498 à 522) ===")
    # Pour chaque ligne du gap, interpolation douce des coordonnées X
    for yi in range(497, 523):
        t = (yi - 497) / (522 - 497)
        # Interpolation Hermite douce (smoothstep)
        s = t * t * (3.0 - 2.0 * t)

        # Colonne gauche
        xl_min = int(66.0 * (1.0 - s) + 108.0 * s)
        xl_max = int(174.0 * (1.0 - s) + 178.0 * s)
        is_plate[yi, xl_min:xl_max] = True

        # Prolongement du liseré néon cyan continu sur le bord extérieur
        is_neon[yi, xl_max-3:xl_max] = True

        # Colonne droite
        xr_min = int(850.0 * (1.0 - s) + 846.0 * s)
        xr_max = int(958.0 * (1.0 - s) + 914.0 * s)
        is_plate[yi, xr_min:xr_max] = True
        is_neon[yi, xr_min:xr_min+3] = True

    # Lissage morphologique de la zone de raccordement pour supprimer toute démarcation
    plate_mask_img = Image.fromarray((is_plate * 255).astype(np.uint8), mode='L')
    smooth_zone = np.zeros((h, w), dtype=bool)
    smooth_zone[485:535, :240] = True
    smooth_zone[485:535, 780:] = True

    blurred_mask = np.array(plate_mask_img.filter(ImageFilter.GaussianBlur(radius=2.5)), dtype=np.float32) / 255.0
    is_plate[smooth_zone] = blurred_mask[smooth_zone] >= 0.45

    print("=== 3. Recalcul de la Heightmap 3D et du Lustre Titane Satiné Unifié ===")
    # Heightmap multi-échelle pour un galbe voluptueux et sans coupure
    mask_full = is_plate | is_neon
    full_mask_img = Image.fromarray((mask_full * 255).astype(np.uint8), mode='L')

    h1 = np.array(full_mask_img.filter(ImageFilter.GaussianBlur(radius=2.0)), dtype=np.float32) / 255.0
    h2 = np.array(full_mask_img.filter(ImageFilter.GaussianBlur(radius=6.0)), dtype=np.float32) / 255.0
    h3 = np.array(full_mask_img.filter(ImageFilter.GaussianBlur(radius=16.0)), dtype=np.float32) / 255.0
    h4 = np.array(full_mask_img.filter(ImageFilter.GaussianBlur(radius=32.0)), dtype=np.float32) / 255.0

    height_map = (h1 * 0.35 + h2 * 0.35 + h3 * 0.20 + h4 * 0.10) * mask_full

    # Galbe sphérique franc sur les dômes de poitrine (575, 255) et (449, 255)
    r_dome = 66.0
    d_dome_l = np.sqrt((x_idx - 575.0)**2 + (y_idx - 255.0)**2) / r_dome
    d_dome_r = np.sqrt((x_idx - 449.0)**2 + (y_idx - 255.0)**2) / r_dome
    sph_l = np.sqrt(np.maximum(0.0, 1.0 - d_dome_l**2)) * (d_dome_l < 1.0)
    sph_r = np.sqrt(np.maximum(0.0, 1.0 - d_dome_r**2)) * (d_dome_r < 1.0)
    height_map += (sph_l + sph_r) * 0.42 * mask_full

    # Galbe cylindrique continu le long de la grande plaque de cuisse unifiée
    cyl_thigh_l = np.sqrt(np.maximum(0.0, 1.0 - ((x_idx - 145.0) / 52.0)**2)) * (np.abs(x_idx - 145.0) < 52.0)
    cyl_thigh_r = np.sqrt(np.maximum(0.0, 1.0 - ((x_idx - 879.0) / 52.0)**2)) * (np.abs(x_idx - 879.0) < 52.0)
    height_map += (cyl_thigh_l + cyl_thigh_r) * 0.30 * mask_full

    # Normales 3D de surface
    dy, dx = np.gradient(height_map * 22.0)
    nz = 1.0
    norm = np.sqrt(dx**2 + dy**2 + nz**2)
    nx, ny, nz = -dx / norm, -dy / norm, nz / norm

    # Éclairage Blinn-Phong Titane Mecha Satiné
    lx, ly, lz = 0.15, -0.62, 0.76
    llen = np.sqrt(lx**2 + ly**2 + lz**2)
    lx, ly, lz = lx/llen, ly/llen, lz/llen

    hx, hy, hz = lx, ly, lz + 1.0
    hlen = np.sqrt(hx**2 + hy**2 + hz**2)
    hx, hy, hz = hx/hlen, hy/hlen, hz/hlen

    dot_l = np.maximum(0.0, nx*lx + ny*ly + nz*lz)
    dot_h = np.maximum(0.0, nx*hx + ny*hy + nz*hz)
    specular = dot_h ** 16.0
    fresnel = (1.0 - nz) ** 2.0

    metal_r = np.clip(62.0 + 52.0 * dot_l + 88.0 * specular + 35.0 * fresnel, 0, 255)
    metal_g = np.clip(102.0 + 72.0 * dot_l + 96.0 * specular + 50.0 * fresnel, 0, 255)
    metal_b = np.clip(152.0 + 75.0 * dot_l + 98.0 * specular + 60.0 * fresnel, 0, 255)

    # Application du matériau métallique
    out_arr = arr.copy()
    is_protected_rivet = is_rivet & (~is_neon)
    apply_plate = is_plate & (~is_protected_rivet) & (~is_neon)

    out_arr[apply_plate, 0] = metal_r[apply_plate]
    out_arr[apply_plate, 1] = metal_g[apply_plate]
    out_arr[apply_plate, 2] = metal_b[apply_plate]

    # Application des néons cyan luminescents (#00f5d4)
    out_arr[is_neon, 0] = 0.0
    out_arr[is_neon, 1] = 245.0
    out_arr[is_neon, 2] = 212.0

    # Lignes d'occlusion ambiante sur les bords extérieurs
    edge_dil = np.array(full_mask_img.filter(ImageFilter.MaxFilter(size=3)), dtype=np.uint8) > 0
    crevice = edge_dil & (~mask_full) & is_uv_mesh
    out_arr[crevice, 0] = np.minimum(out_arr[crevice, 0], 14.0)
    out_arr[crevice, 1] = np.minimum(out_arr[crevice, 1], 18.0)
    out_arr[crevice, 2] = np.minimum(out_arr[crevice, 2], 28.0)

    # Sauvegarde finale
    final_img = Image.fromarray(out_arr.astype(np.uint8), mode='RGBA')
    final_img.save('packages/compagnon-desktop/overlay/vrm/body_skin_android.png')
    final_img.save('packages/cortex/compagnon_ui/public/vrm/body_skin_android.png')
    print("=== Plaques de cuisse jointes et lissées avec succès ! ===")

if __name__ == '__main__':
    join_thigh_plates()
