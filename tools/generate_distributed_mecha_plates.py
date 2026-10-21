import numpy as np
from PIL import Image, ImageFilter, ImageDraw

def generate_mecha_texture():
    print("1. Chargement des bases...")
    # Base v15 à 1024x1024 pour fond de combinaison sombre et striures musculaires
    base_img = Image.open('tools/skin_v15.png').resize((1024, 1024), Image.Resampling.LANCZOS).convert('RGBA')
    base_arr = np.array(base_img, dtype=np.float32)

    # Image courante pour récupérer les ongles, rivets originaux et mains
    cur_img = Image.open('packages/compagnon-desktop/overlay/vrm/body_skin_android.png').convert('RGBA')
    cur_arr = np.array(cur_img, dtype=np.float32)

    h, w = 1024, 1024
    mask = np.zeros((h, w), dtype=bool)
    y_grid, x_grid = np.ogrid[:h, :w]

    print("2. Construction du masque anatomique mecha...")
    # --- A. BUSTE & POITRINE ---
    # Dômes pectoraux gauche et droit
    d_dome_l = np.sqrt((x_grid - 575.0)**2 + (y_grid - 255.0)**2)
    d_dome_r = np.sqrt((x_grid - 449.0)**2 + (y_grid - 255.0)**2)
    mask |= (d_dome_l <= 65.0) | (d_dome_r <= 65.0)

    # Plastron central supérieur (sternum)
    mask |= (x_grid >= 460) & (x_grid <= 564) & (y_grid >= 170) & (y_grid <= 270)

    # --- B. ABDOMEN CENTRAL FUSELÉ (flancs dégagés !) ---
    for y in range(295, 490):
        t = (y - 295) / (490 - 295)
        w_half = int(52 * (1.0 - 0.35 * t))
        mask[y, 512-w_half:512+w_half] = True

    # --- C. COQUE PELVIENNE EN V ---
    for y in range(495, 575):
        t = (y - 495) / (575 - 495)
        w_half = int(48 * (1.0 - 0.70 * t))
        mask[y, 512-w_half:512+w_half] = True

    # Coques latérales de hanches fines
    mask |= (x_grid >= 390) & (x_grid <= 430) & (y_grid >= 510) & (y_grid <= 560)
    mask |= (x_grid >= 594) & (x_grid <= 634) & (y_grid >= 510) & (y_grid <= 560)

    # --- D. BRAS & ÉPAULES ---
    # Épaules deltoïdes
    mask |= (x_grid >= 865) & (x_grid <= 955) & (y_grid >= 45) & (y_grid <= 105)
    mask |= (x_grid >= 69) & (x_grid <= 159) & (y_grid >= 45) & (y_grid <= 105)

    # Biceps (Upper Arm)
    mask |= (x_grid >= 870) & (x_grid <= 945) & (y_grid >= 115) & (y_grid <= 220)
    mask |= (x_grid >= 79) & (x_grid <= 154) & (y_grid >= 115) & (y_grid <= 220)

    # Avant-bras (Forearm shield)
    mask |= (x_grid >= 865) & (x_grid <= 940) & (y_grid >= 298) & (y_grid <= 430)
    mask |= (x_grid >= 84) & (x_grid <= 159) & (y_grid >= 298) & (y_grid <= 430)

    # --- E. JAMBES ---
    # Plaques fémorales (Cuisses avant)
    mask |= (x_grid >= 804) & (x_grid <= 880) & (y_grid >= 550) & (y_grid <= 660)
    mask |= (x_grid >= 144) & (x_grid <= 220) & (y_grid >= 550) & (y_grid <= 660)

    # Genouillères / Rotules articulées
    d_knee_l = np.sqrt(((x_grid - 846.0)/24.0)**2 + ((y_grid - 726.0)/18.0)**2)
    d_knee_r = np.sqrt(((x_grid - 178.0)/24.0)**2 + ((y_grid - 726.0)/18.0)**2)
    mask |= (d_knee_l <= 1.0) | (d_knee_r <= 1.0)

    # Plaques tibiales (Tibias avant)
    mask |= (x_grid >= 806) & (x_grid <= 856) & (y_grid >= 782) & (y_grid <= 940)
    mask |= (x_grid >= 168) & (x_grid <= 218) & (y_grid >= 782) & (y_grid <= 940)

    # Plaques de mollets externes
    mask |= (x_grid >= 630) & (x_grid <= 710) & (y_grid >= 800) & (y_grid <= 920)
    mask |= (x_grid >= 314) & (x_grid <= 394) & (y_grid >= 800) & (y_grid <= 920)

    # Protection zone pieds, ongles et mains
    is_protected_bottom = np.zeros((h, w), dtype=bool)
    is_protected_bottom[710:1024, 220:805] = True
    mask &= (~is_protected_bottom)

    # Symétrisation parfaite
    right_half = mask[:, 512:]
    left_mirrored = np.fliplr(right_half)
    mask[:, :512] = left_mirrored

    print(f"Total pixels de plaques actives: {np.count_nonzero(mask)}")

    # 3. Modelé 3D de hauteur (Heightmap Blinn-Phong)
    mask_img = Image.fromarray((mask * 255).astype(np.uint8), mode='L')
    h1 = np.array(mask_img.filter(ImageFilter.GaussianBlur(radius=2.0)), dtype=np.float32) / 255.0
    h2 = np.array(mask_img.filter(ImageFilter.GaussianBlur(radius=6.0)), dtype=np.float32) / 255.0
    h3 = np.array(mask_img.filter(ImageFilter.GaussianBlur(radius=15.0)), dtype=np.float32) / 255.0
    h4 = np.array(mask_img.filter(ImageFilter.GaussianBlur(radius=30.0)), dtype=np.float32) / 255.0

    height = (h1 * 0.35 + h2 * 0.35 + h3 * 0.20 + h4 * 0.10) * mask

    # Dômes sphériques pectoraux
    r_dome = 65.0
    d_l = np.sqrt((x_grid - 575.0)**2 + (y_grid - 255.0)**2) / r_dome
    d_r = np.sqrt((x_grid - 449.0)**2 + (y_grid - 255.0)**2) / r_dome
    sphere_l = np.sqrt(np.maximum(0.0, 1.0 - d_l**2)) * (d_l < 1.0)
    sphere_r = np.sqrt(np.maximum(0.0, 1.0 - d_r**2)) * (d_r < 1.0)
    height += (sphere_l + sphere_r) * 0.40 * mask

    # Rotules sphériques de genoux
    knee_sph_l = np.maximum(0.0, 1.0 - d_knee_l) * (d_knee_l <= 1.0)
    knee_sph_r = np.maximum(0.0, 1.0 - d_knee_r) * (d_knee_r <= 1.0)
    height += (knee_sph_l + knee_sph_r) * 0.30 * mask

    # Galbe cylindrique sur les membres
    cyl_arm_l = np.sqrt(np.maximum(0.0, 1.0 - ((x_grid - 905.0) / 45.0)**2)) * (np.abs(x_grid - 905.0) < 45.0)
    cyl_arm_r = np.sqrt(np.maximum(0.0, 1.0 - ((x_grid - 119.0) / 45.0)**2)) * (np.abs(x_grid - 119.0) < 45.0)
    height += (cyl_arm_l + cyl_arm_r) * 0.25 * mask

    cyl_leg_l = np.sqrt(np.maximum(0.0, 1.0 - ((x_grid - 842.0) / 45.0)**2)) * (np.abs(x_grid - 842.0) < 45.0)
    cyl_leg_r = np.sqrt(np.maximum(0.0, 1.0 - ((x_grid - 182.0) / 45.0)**2)) * (np.abs(x_grid - 182.0) < 45.0)
    height += (cyl_leg_l + cyl_leg_r) * 0.25 * mask

    # 4. Normales 3D de surface
    dy, dx = np.gradient(height * 20.0)
    nz = 1.0
    norm = np.sqrt(dx**2 + dy**2 + nz**2)
    nx, ny, nz = -dx / norm, -dy / norm, nz / norm

    # 5. Éclairage Blinn-Phong Titane Mecha unifié
    lx, ly, lz = 0.15, -0.60, 0.78
    llen = np.sqrt(lx**2 + ly**2 + lz**2)
    lx, ly, lz = lx/llen, ly/llen, lz/llen

    hx, hy, hz = lx, ly, lz + 1.0
    hlen = np.sqrt(hx**2 + hy**2 + hz**2)
    hx, hy, hz = hx/hlen, hy/hlen, hz/hlen

    dot_l = np.maximum(0.0, nx*lx + ny*ly + nz*lz)
    dot_h = np.maximum(0.0, nx*hx + ny*hy + nz*hz)
    specular = dot_h ** 14.0
    fresnel = (1.0 - nz) ** 2.0

    metal_r = np.clip(54.0 + 48.0 * dot_l + 85.0 * specular + 35.0 * fresnel, 0, 255)
    metal_g = np.clip(88.0 + 68.0 * dot_l + 95.0 * specular + 50.0 * fresnel, 0, 255)
    metal_b = np.clip(138.0 + 72.0 * dot_l + 95.0 * specular + 60.0 * fresnel, 0, 255)

    # 6. Assemblage sur la combinaison sombre de base
    out_arr = base_arr.copy()
    out_arr[mask, 0] = metal_r[mask]
    out_arr[mask, 1] = metal_g[mask]
    out_arr[mask, 2] = metal_b[mask]

    # 7. Lignes de joints creux noires biseautées autour des plaques (chanfreins nets mecha)
    edge_dil = np.array(mask_img.filter(ImageFilter.MaxFilter(size=5)), dtype=np.uint8) > 0
    crevice = edge_dil & (~mask) & (~is_protected_bottom)
    out_arr[crevice, 0] = np.minimum(out_arr[crevice, 0], 15.0)
    out_arr[crevice, 1] = np.minimum(out_arr[crevice, 1], 18.0)
    out_arr[crevice, 2] = np.minimum(out_arr[crevice, 2], 26.0)

    # 8. Liserés néon cyan luminescents (#00f5d4) sur les découpes clés
    # Dômes de poitrine
    neon_dome_l = (d_dome_l >= 58.0) & (d_dome_l <= 64.0) & mask
    neon_dome_r = (d_dome_r >= 58.0) & (d_dome_r <= 64.0) & mask

    # Liserés verticaux le long de la plaque ventrale
    neon_ventre = np.zeros((h, w), dtype=bool)
    for y in range(300, 480):
        t = (y - 295) / (490 - 295)
        w_half = int(52 * (1.0 - 0.35 * t))
        neon_ventre[y, 512-w_half:512-w_half+3] = True
        neon_ventre[y, 512+w_half-3:512+w_half] = True
    neon_ventre &= mask

    # Liseré en V sur la coque pelvienne
    neon_pelvis = np.zeros((h, w), dtype=bool)
    for y in range(500, 570):
        t = (y - 495) / (575 - 495)
        w_half = int(48 * (1.0 - 0.70 * t))
        neon_pelvis[y, 512-w_half:512-w_half+3] = True
        neon_pelvis[y, 512+w_half-3:512+w_half] = True
    neon_pelvis &= mask

    # Anneau néon sur les rotules de genou
    neon_knee_l = (d_knee_l >= 0.82) & (d_knee_l <= 0.98) & mask
    neon_knee_r = (d_knee_r >= 0.82) & (d_knee_r <= 0.98) & mask

    neon_all = neon_dome_l | neon_dome_r | neon_ventre | neon_pelvis | neon_knee_l | neon_knee_r

    out_arr[neon_all, 0] = 0.0
    out_arr[neon_all, 1] = 245.0
    out_arr[neon_all, 2] = 212.0

    # 9. Réinjecter les ongles et mains originales protégées
    out_arr[is_protected_bottom] = cur_arr[is_protected_bottom]

    final_img = Image.fromarray(out_arr.astype(np.uint8), mode='RGBA')
    final_img.save('packages/compagnon-desktop/overlay/vrm/body_skin_android.png')
    final_img.save('packages/cortex/compagnon_ui/public/vrm/body_skin_android.png')
    print("Texture redistribuée mecha v21 générée avec succès !")

if __name__ == '__main__':
    generate_mecha_texture()
