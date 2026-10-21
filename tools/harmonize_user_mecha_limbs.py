import numpy as np
from PIL import Image, ImageFilter, ImageDraw

def build_harmonized_mecha():
    print("=== 1. Chargement de la texture maître de l'utilisateur ===")
    user_img = Image.open('/home/lbg/.gemini/antigravity-ide/brain/1165e65b-2952-49ad-8ee9-8135d868d941/.user_uploaded/media_1792615448352.png').convert('RGBA')
    user_arr = np.array(user_img, dtype=np.float32)

    green_im = Image.open('/home/lbg/.gemini/antigravity-ide/brain/1165e65b-2952-49ad-8ee9-8135d868d941/.user_uploaded/media_1792615525290.png')
    green_arr = np.array(green_im)
    is_uv_mesh = (green_arr[:, :, 1] > 50) & (green_arr[:, :, 0] < 50) & (green_arr[:, :, 2] < 50)

    h, w = 1024, 1024
    y_idx, x_idx = np.ogrid[:h, :w]

    # Extraction des masques de l'utilisateur
    r, g, b = user_arr[:,:,0], user_arr[:,:,1], user_arr[:,:,2]
    is_neon_orig = (g > 200) & (b > 180) & (r < 50)
    is_plate_orig = (b > 160) & (g > 120) & (r < 180)
    is_rivet_orig = (r < 40) & (g < 40) & (b < 60)

    # Création du canvas de travail
    out_arr = user_arr.copy()
    mask_plates = is_plate_orig.copy()
    mask_neons = is_neon_orig.copy()

    print("=== 2. Ajout de la correspondance stylistique sur les membres (Bras & Jambes) ===")
    
    # --- A. AVANT-BRAS (Forearms) : Y in [292..498], Left column X < 240, Right column X > 780 ---
    # Ajout des liserés néon cyan sur les bords et fentes de l'avant-bras assorties à l'épaule
    for yi in range(305, 480):
        # Trouver les bords gauche et droit de la plaque d'avant-bras à cette ligne
        row_l = np.where(mask_plates[yi, :240])[0]
        if len(row_l) > 10:
            xl_min, xl_max = row_l.min(), row_l.max()
            mask_neons[yi, xl_min:xl_min+2] = True
            mask_neons[yi, xl_max-2:xl_max] = True
            # Fente horizontale médiane à mi-avant-bras (Y=390)
            if yi in [390, 391]:
                mask_neons[yi, xl_min+8:xl_max-8] = True

        row_r = np.where(mask_plates[yi, 780:])[0]
        if len(row_r) > 10:
            xr_min, xr_max = row_r.min() + 780, row_r.max() + 780
            mask_neons[yi, xr_min:xr_min+2] = True
            mask_neons[yi, xr_max-2:xr_max] = True
            if yi in [390, 391]:
                mask_neons[yi, xr_min+8:xr_max-8] = True

    # --- B. CUISSES (Thighs) : Y in [520..675] ---
    # Ajout du liseré néon cyan de contour et de la fente aérodynamique le long du vaste externe
    for yi in range(530, 670):
        row_l = np.where(mask_plates[yi, :240])[0]
        if len(row_l) > 15:
            xl_min, xl_max = row_l.min(), row_l.max()
            # Liseré extérieur néon cyan
            mask_neons[yi, xl_max-3:xl_max] = True
            # Fente aérodynamique médiane avec néon cyan (Y: 570..640)
            if 570 <= yi <= 640:
                pos_mid = int(xl_min * 0.4 + xl_max * 0.6)
                mask_neons[yi, pos_mid:pos_mid+2] = True

        row_r = np.where(mask_plates[yi, 780:])[0]
        if len(row_r) > 15:
            xr_min, xr_max = row_r.min() + 780, row_r.max() + 780
            mask_neons[yi, xr_min:xr_min+3] = True
            if 570 <= yi <= 640:
                pos_mid = int(xr_min * 0.6 + xr_max * 0.4)
                mask_neons[yi, pos_mid:pos_mid+2] = True

    # --- C. ROTULES DE GENOUX (Knees) : Y in [685..750] ---
    # Rotules circulaires mécaniques cerclées de néon cyan (assorties aux rivets d'épaules et de hanches)
    d_kn_l = np.sqrt(((x_idx - 176.0) / 24.0)**2 + ((y_idx - 720.0) / 22.0)**2)
    d_kn_r = np.sqrt(((x_idx - 848.0) / 24.0)**2 + ((y_idx - 720.0) / 22.0)**2)
    is_knee_rotula = (d_kn_l <= 1.0) | (d_kn_r <= 1.0)
    mask_plates |= is_knee_rotula
    
    # Anneau néon cyan autour de la rotule
    ring_knee = ((d_kn_l >= 0.82) & (d_kn_l <= 0.98)) | ((d_kn_r >= 0.82) & (d_kn_r <= 0.98))
    mask_neons |= ring_knee

    # Rivet mécanique central dans la rotule (cercle noir avec point bleu)
    center_knee = (d_kn_l <= 0.28) | (d_kn_r <= 0.28)
    ring_rivet = ((d_kn_l >= 0.28) & (d_kn_l <= 0.45)) | ((d_kn_r >= 0.28) & (d_kn_r <= 0.45))
    out_arr[ring_rivet, 0:3] = [15.0, 18.0, 26.0]

    # --- D. TIBIAS ET MOLLETS (Shins & Calves) : Y in [765..980] ---
    # Liseré néon cyan descendant le long de la crête tibiale
    for yi in range(770, 960):
        row_l = np.where(mask_plates[yi, :240])[0]
        if len(row_l) > 10:
            xl_min, xl_max = row_l.min(), row_l.max()
            # Liseré néon sur l'arête avant
            pos_crest_l = int(xl_min * 0.3 + xl_max * 0.7)
            mask_neons[yi, pos_crest_l:pos_crest_l+2] = True

        row_r = np.where(mask_plates[yi, 780:])[0]
        if len(row_r) > 10:
            xr_min, xr_max = row_r.min() + 780, row_r.max() + 780
            pos_crest_r = int(xr_min * 0.7 + xr_max * 0.3)
            mask_neons[yi, pos_crest_r:pos_crest_r+2] = True

    print("=== 3. Calcul de la Heightmap 3D et du Lustre Titane Satiné Unifié ===")
    mask_img = Image.fromarray((mask_plates * 255).astype(np.uint8), mode='L')
    
    # Lissage multi-échelle pour galbe volumétrique
    h1 = np.array(mask_img.filter(ImageFilter.GaussianBlur(radius=2.0)), dtype=np.float32) / 255.0
    h2 = np.array(mask_img.filter(ImageFilter.GaussianBlur(radius=6.0)), dtype=np.float32) / 255.0
    h3 = np.array(mask_img.filter(ImageFilter.GaussianBlur(radius=16.0)), dtype=np.float32) / 255.0
    h4 = np.array(mask_img.filter(ImageFilter.GaussianBlur(radius=32.0)), dtype=np.float32) / 255.0
    
    height_map = (h1 * 0.35 + h2 * 0.35 + h3 * 0.20 + h4 * 0.10) * mask_plates

    # Galbe sphérique franc sur les dômes de poitrine (575, 255) et (449, 255)
    r_dome = 66.0
    d_dome_l = np.sqrt((x_idx - 575.0)**2 + (y_idx - 255.0)**2) / r_dome
    d_dome_r = np.sqrt((x_idx - 449.0)**2 + (y_idx - 255.0)**2) / r_dome
    sph_l = np.sqrt(np.maximum(0.0, 1.0 - d_dome_l**2)) * (d_dome_l < 1.0)
    sph_r = np.sqrt(np.maximum(0.0, 1.0 - d_dome_r**2)) * (d_dome_r < 1.0)
    height_map += (sph_l + sph_r) * 0.42 * mask_plates

    # Galbe cylindrique sur les membres (bras et jambes)
    cyl_arm_l = np.sqrt(np.maximum(0.0, 1.0 - ((x_idx - 910.0) / 45.0)**2)) * (np.abs(x_idx - 910.0) < 45.0)
    cyl_arm_r = np.sqrt(np.maximum(0.0, 1.0 - ((x_idx - 114.0) / 45.0)**2)) * (np.abs(x_idx - 114.0) < 45.0)
    height_map += (cyl_arm_l + cyl_arm_r) * 0.28 * mask_plates

    cyl_leg_l = np.sqrt(np.maximum(0.0, 1.0 - ((x_idx - 845.0) / 50.0)**2)) * (np.abs(x_idx - 845.0) < 50.0)
    cyl_leg_r = np.sqrt(np.maximum(0.0, 1.0 - ((x_idx - 179.0) / 50.0)**2)) * (np.abs(x_idx - 179.0) < 50.0)
    height_map += (cyl_leg_l + cyl_leg_r) * 0.28 * mask_plates

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

    # Teinte Titane Mecha Bleuté riche (Fidèle à l'image 3 de l'utilisateur)
    metal_r = np.clip(62.0 + 52.0 * dot_l + 88.0 * specular + 35.0 * fresnel, 0, 255)
    metal_g = np.clip(102.0 + 72.0 * dot_l + 96.0 * specular + 50.0 * fresnel, 0, 255)
    metal_b = np.clip(152.0 + 75.0 * dot_l + 98.0 * specular + 60.0 * fresnel, 0, 255)

    # Application du matériau métallique sur TOUTES les plaques (membres et torse)
    # en préservant les rivets originaux et le fond de combinaison sombre
    is_protected_rivet = is_rivet_orig & (~is_neon_orig)
    apply_plate = mask_plates & (~is_protected_rivet) & (~mask_neons)

    out_arr[apply_plate, 0] = metal_r[apply_plate]
    out_arr[apply_plate, 1] = metal_g[apply_plate]
    out_arr[apply_plate, 2] = metal_b[apply_plate]

    # Injection des néons cyan luminescents purs (#00f5d4)
    out_arr[mask_neons, 0] = 0.0
    out_arr[mask_neons, 1] = 245.0
    out_arr[mask_neons, 2] = 212.0

    # Lignes d'occlusion ambiante noires autour des découpes
    edge_dil = np.array(mask_img.filter(ImageFilter.MaxFilter(size=3)), dtype=np.uint8) > 0
    crevice = edge_dil & (~mask_plates) & is_uv_mesh
    out_arr[crevice, 0] = np.minimum(out_arr[crevice, 0], 14.0)
    out_arr[crevice, 1] = np.minimum(out_arr[crevice, 1], 18.0)
    out_arr[crevice, 2] = np.minimum(out_arr[crevice, 2], 28.0)

    # Sauvegarde finale
    final_img = Image.fromarray(out_arr.astype(np.uint8), mode='RGBA')
    final_img.save('packages/compagnon-desktop/overlay/vrm/body_skin_android.png')
    final_img.save('packages/cortex/compagnon_ui/public/vrm/body_skin_android.png')
    print("=== Texture Mecha Harmonieuse (Correspondance Torse <-> Membres) générée avec succès ! ===")

if __name__ == '__main__':
    build_harmonized_mecha()
