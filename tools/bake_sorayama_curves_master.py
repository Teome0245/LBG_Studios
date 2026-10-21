import numpy as np
from PIL import Image, ImageFilter

def generate_sorayama_curved_master():
    print("=== 1. Initialisation des textures et gabarit UV ===")
    h, w = 1024, 1024

    # Gabarit UV vert pour borner 100% de la carrosserie au maillage réel
    green_im = Image.open('/home/lbg/.gemini/antigravity-ide/brain/1165e65b-2952-49ad-8ee9-8135d868d941/.user_uploaded/media_1792613031209.png')
    green_arr = np.array(green_im)
    is_uv_mesh = (green_arr[:, :, 1] > 50) & (green_arr[:, :, 0] < 50) & (green_arr[:, :, 2] < 50)

    # Récupération des mains, phalanges et ongles bicolores
    cur_img = Image.open('packages/compagnon-desktop/overlay/vrm/body_skin_android.png').convert('RGBA')
    cur_arr = np.array(cur_img, dtype=np.float32)

    # Grilles de coordonnées
    y_idx, x_idx = np.ogrid[:h, :w]

    # Fond de sous-combinaison sombre mécatronique (Anthracite bleuté texturé)
    dark_suit = np.zeros((h, w, 4), dtype=np.float32)
    dark_suit[:, :, 0] = 16.0
    dark_suit[:, :, 1] = 22.0
    dark_suit[:, :, 2] = 32.0
    dark_suit[:, :, 3] = 255.0

    # Fines nervures musculaires synthétiques dans les creux
    fiber = np.sin((x_idx + y_idx * 0.4) * 0.35) * 3.5 + np.sin((y_idx - x_idx * 0.25) * 0.5) * 2.5
    dark_suit[:, :, 0] += fiber
    dark_suit[:, :, 1] += fiber * 1.15
    dark_suit[:, :, 2] += fiber * 1.4

    # Initialisation des cartes de plaques, de hauteur et de lignes
    mask_chrome = np.zeros((h, w), dtype=bool)
    height_map = np.zeros((h, w), dtype=np.float32)
    panel_lines = np.zeros((h, w), dtype=bool)
    neon_lines = np.zeros((h, w), dtype=bool)

    print("=== 2. Sculpture des Courbes Organiques Sorayama (Poitrine & Buste) ===")
    # A. Dômes de poitrine voluptueux (Goutte d'eau galbée / Teardrop)
    # Centres: gauche=(575, 255), droite=(449, 255)
    r_x, r_y = 66.0, 64.0
    d_l = np.sqrt(((x_idx - 575.0) / r_x)**2 + ((y_idx - 255.0) / r_y)**2)
    d_r = np.sqrt(((x_idx - 449.0) / r_x)**2 + ((y_idx - 255.0) / r_y)**2)
    is_breast = (d_l <= 1.0) | (d_r <= 1.0)
    mask_chrome |= is_breast

    # Galbe sphérique franc
    h_breast_l = np.sqrt(np.maximum(0.0, 1.0 - d_l**2)) * (d_l <= 1.0)
    h_breast_r = np.sqrt(np.maximum(0.0, 1.0 - d_r**2)) * (d_r <= 1.0)
    height_map += (h_breast_l + h_breast_r) * 0.65

    # Liseré néon discret sur la courbure externe
    neon_lines |= ((d_l >= 0.90) & (d_l <= 0.98)) | ((d_r >= 0.90) & (d_r <= 0.98))

    # B. Plastron décolleté & clavicules (arche courbée fluide en V doux au-dessus des seins)
    for yi in range(165, 260):
        t = (yi - 165) / (260 - 165)
        # Courbe évasée en cloche inversée
        hw = 30.0 + 32.0 * np.sin(t * np.pi * 0.5)
        mask_chrome[yi, int(512-hw):int(512+hw)] = True
        height_map[yi, int(512-hw):int(512+hw)] += 0.35 * (1.0 - (np.abs(x_idx[0, int(512-hw):int(512+hw)] - 512.0) / hw)**2)

    # C. Arceau sous-mammaire (pli concave continu)
    for xi in range(380, 645):
        # Arc de cercle sous la poitrine
        dx_c = np.abs(xi - 512.0)
        y_arch = int(305.0 + 12.0 * np.cos((xi - 512.0) / 130.0 * np.pi * 0.5))
        mask_chrome[y_arch-3:y_arch+4, xi] = True
        height_map[y_arch-3:y_arch+4, xi] += 0.38
        panel_lines[y_arch+4:y_arch+6, xi] = True

    print("=== 3. Sculpture de la Taille de Guêpe en S-Curve & Pelvis ===")
    # D. Abdomen en courbe de sablier sensuelle (Hourglass S-curve)
    for yi in range(318, 492):
        t = (yi - 318) / (492 - 318) # 0 (sous seins) à 1 (nombril/hanches)
        # Courbe en S : large en haut (~66 px), cambrure fine au milieu (~36 px), évasement sur le bassin (~72 px)
        s_curve = 36.0 + 30.0 * (1.0 - np.sin(t * np.pi))**1.4 + 6.0 * t
        mask_chrome[yi, int(512-s_curve):int(512+s_curve)] = True
        
        # Galbe bombé abdominal central
        dx_val = np.abs(x_idx[0, int(512-s_curve):int(512+s_curve)] - 512.0) / s_curve
        height_map[yi, int(512-s_curve):int(512+s_curve)] += (1.0 - dx_val**2) * 0.45

        # 3 Fentes aérodynamiques incurvées horizontales
        if yi in [362, 408, 452]:
            panel_lines[yi:yi+2, int(512-s_curve+4):int(512+s_curve-4)] = True

    # E. Coque pelvienne profilée en ogive gothique adoucie (Pelvis Shield)
    for yi in range(492, 578):
        t = (yi - 492) / (578 - 492)
        # Courbe en goutte d'eau descendante vers l'entrejambe
        hw_pelvis = 68.0 * (1.0 - t**0.85)
        mask_chrome[yi, int(512-hw_pelvis):int(512+hw_pelvis)] = True
        height_map[yi, int(512-hw_pelvis):int(512+hw_pelvis)] += 0.42 * (1.0 - t * 0.5)

    # Liseré néon cyan galbé sur le bord de l'ogive pelvienne
    for yi in range(496, 572):
        t = (yi - 492) / (578 - 492)
        hw_pelvis = 68.0 * (1.0 - t**0.85)
        if hw_pelvis >= 3.0:
            neon_lines[yi, int(512-hw_pelvis):int(512-hw_pelvis+2)] = True
            neon_lines[yi, int(512+hw_pelvis-2):int(512+hw_pelvis)] = True

    # F. Carapaces de hanches latérales galbées (ailes iliaques)
    # Courbe ovale arquée suivant la crête de hanche
    d_hip_l = np.sqrt(((x_idx - 616.0) / 24.0)**2 + ((y_idx - 530.0) / 28.0)**2)
    d_hip_r = np.sqrt(((x_idx - 408.0) / 24.0)**2 + ((y_idx - 530.0) / 28.0)**2)
    is_hips = (d_hip_l <= 1.0) | (d_hip_r <= 1.0)
    mask_chrome |= is_hips
    height_map += (np.maximum(0.0, 1.0 - d_hip_l) * (d_hip_l <= 1.0) + np.maximum(0.0, 1.0 - d_hip_r) * (d_hip_r <= 1.0)) * 0.35

    print("=== 4. Sculpture du Dos 360° (Scapula, Colonne & Fessiers) ===")
    # G. Omoplates (Scapula) en ailes profilées galbées (Y: 175..305)
    for yi in range(175, 305):
        t = (yi - 175) / (305 - 175)
        # Forme d'amande ailée
        w_wing = 52.0 * np.sin(t * np.pi)**0.8
        cx_wing_r, cx_wing_l = 310.0, 714.0
        mask_chrome[yi, int(cx_wing_r-w_wing):int(cx_wing_r+w_wing)] = True
        mask_chrome[yi, int(cx_wing_l-w_wing):int(cx_wing_l+w_wing)] = True
        height_map[yi, int(cx_wing_r-w_wing):int(cx_wing_r+w_wing)] += 0.38
        height_map[yi, int(cx_wing_l-w_wing):int(cx_wing_l+w_wing)] += 0.38

    # H. Colonne vertébrale articulée Sorayama (chaîne de modules ovoïdes bombés)
    # Le long de la couture dorsale médiane (X: 246..275 et 749..778)
    for yi in range(170, 480):
        t_disc = (yi % 24) / 24.0
        # Forme arrondie de chaque vertèbre
        rad_v = 13.0 * np.sin(t_disc * np.pi)
        if rad_v > 1.0:
            mask_chrome[yi, int(260-rad_v):int(260+rad_v)] = True
            mask_chrome[yi, int(764-rad_v):int(764+rad_v)] = True
            height_map[yi, int(260-rad_v):int(260+rad_v)] += 0.45
            height_map[yi, int(764-rad_v):int(764+rad_v)] += 0.45
        
        # Disque intervertébral noir
        if yi % 24 in [0, 1, 23]:
            panel_lines[yi, 246:275] = True
            panel_lines[yi, 749:778] = True
        
        # Diodes neurales cyan au centre de chaque module
        if yi % 24 in [10, 11, 12, 13]:
            neon_lines[yi, 259:262] = True
            neon_lines[yi, 763:766] = True

    # I. Double coque fessière voluptueuse Sorayama (Deux dômes galbés parfaits)
    d_butt_r = np.sqrt(((x_idx - 306.0) / 48.0)**2 + ((y_idx - 575.0) / 54.0)**2)
    d_butt_l = np.sqrt(((x_idx - 718.0) / 48.0)**2 + ((y_idx - 575.0) / 54.0)**2)
    is_buttock = (d_butt_r <= 1.0) | (d_butt_l <= 1.0)
    mask_chrome |= is_buttock
    h_butt_r = np.sqrt(np.maximum(0.0, 1.0 - d_butt_r**2)) * (d_butt_r <= 1.0)
    h_butt_l = np.sqrt(np.maximum(0.0, 1.0 - d_butt_l**2)) * (d_butt_l <= 1.0)
    height_map += (h_butt_r + h_butt_l) * 0.58

    # Sillon inter-fessier mécatronique
    panel_lines[520:630, 246:252] = True
    panel_lines[520:630, 772:778] = True

    print("=== 5. Sculpture des Bras, Épaules & Coudes en Courbes Fluides ===")
    # A. Coques deltoïdes des épaules (Demi-sphères galbées épousant le sommet)
    d_sh_l = np.sqrt(((x_idx - 912.0) / 42.0)**2 + ((y_idx - 75.0) / 36.0)**2)
    d_sh_r = np.sqrt(((x_idx - 112.0) / 42.0)**2 + ((y_idx - 75.0) / 36.0)**2)
    is_shoulder = (d_sh_l <= 1.0) | (d_sh_r <= 1.0)
    mask_chrome |= is_shoulder
    height_map += (np.sqrt(np.maximum(0.0, 1.0 - d_sh_l**2)) * (d_sh_l <= 1.0) + np.sqrt(np.maximum(0.0, 1.0 - d_sh_r**2)) * (d_sh_r <= 1.0)) * 0.40

    # B. Biceps fuselés en amande (Y: 115..225)
    for yi in range(115, 225):
        t = (yi - 115) / (225 - 115)
        hw_arm = 38.0 * np.sin(t * np.pi)**0.75
        mask_chrome[yi, int(910-hw_arm):int(910+hw_arm)] = True
        mask_chrome[yi, int(114-hw_arm):int(114+hw_arm)] = True
        height_map[yi, int(910-hw_arm):int(910+hw_arm)] += 0.38
        height_map[yi, int(114-hw_arm):int(114+hw_arm)] += 0.38

    # C. Rotules de coudes concentriques circulaires (Y: 236..276)
    d_elb_l = np.sqrt(((x_idx - 910.0) / 22.0)**2 + ((y_idx - 256.0) / 20.0)**2)
    d_elb_r = np.sqrt(((x_idx - 114.0) / 22.0)**2 + ((y_idx - 256.0) / 20.0)**2)
    is_elbow = (d_elb_l <= 1.0) | (d_elb_r <= 1.0)
    mask_chrome |= is_elbow
    height_map += (np.maximum(0.0, 1.0 - d_elb_l) * (d_elb_l <= 1.0) + np.maximum(0.0, 1.0 - d_elb_r) * (d_elb_r <= 1.0)) * 0.40
    # Cerclage d'ombre autour de la rotule
    panel_lines |= ((d_elb_l >= 0.90) & (d_elb_l <= 1.05)) | ((d_elb_r >= 0.90) & (d_elb_r <= 1.05))

    # D. Avant-bras profilés en fuseaux effilés (Y: 290..430)
    for yi in range(290, 430):
        t = (yi - 290) / (430 - 290)
        hw_fa = 34.0 * np.sin(t * np.pi * 0.9 + 0.1)**0.75
        mask_chrome[yi, int(908-hw_fa):int(908+hw_fa)] = True
        mask_chrome[yi, int(116-hw_fa):int(116+hw_fa)] = True
        height_map[yi, int(908-hw_fa):int(908+hw_fa)] += 0.36
        height_map[yi, int(116-hw_fa):int(116+hw_fa)] += 0.36

    print("=== 6. Sculpture des Cuisses, Genoux & Mollets en Fuseaux Évasés ===")
    # A. Plaques fémorales des cuisses en goutte d'eau profilée (Y: 525..675)
    for yi in range(525, 675):
        t = (yi - 525) / (675 - 525)
        # Galbe musculaire voluptueux des quadriceps
        hw_thigh = 45.0 * np.sin(t * np.pi)**0.72
        mask_chrome[yi, int(842-hw_thigh):int(842+hw_thigh)] = True
        mask_chrome[yi, int(182-hw_thigh):int(182+hw_thigh)] = True
        height_map[yi, int(842-hw_thigh):int(842+hw_thigh)] += 0.46
        height_map[yi, int(182-hw_thigh):int(182+hw_thigh)] += 0.46

    # Fentes courbées aérodynamiques sur l'extérieur de la cuisse
    for yi in range(550, 650):
        t = (yi - 525) / (675 - 525)
        hw_thigh = 45.0 * np.sin(t * np.pi)**0.72
        pos_line_l = int(842 + hw_thigh * 0.65)
        pos_line_r = int(182 - hw_thigh * 0.65)
        panel_lines[yi, pos_line_l:pos_line_l+2] = True
        panel_lines[yi, pos_line_r-2:pos_line_r] = True

    # B. Rotules de genoux concentriques Sorayama (Y: 694..750)
    d_kn_l = np.sqrt(((x_idx - 846.0) / 28.0)**2 + ((y_idx - 722.0) / 25.0)**2)
    d_kn_r = np.sqrt(((x_idx - 178.0) / 28.0)**2 + ((y_idx - 722.0) / 25.0)**2)
    is_knee = (d_kn_l <= 1.0) | (d_kn_r <= 1.0)
    mask_chrome |= is_knee
    height_map += (np.sqrt(np.maximum(0.0, 1.0 - d_kn_l**2)) * (d_kn_l <= 1.0) + np.sqrt(np.maximum(0.0, 1.0 - d_kn_r**2)) * (d_kn_r <= 1.0)) * 0.50
    # Anneau néon cyan autour de la rotule
    neon_lines |= ((d_kn_l >= 0.82) & (d_kn_l <= 0.96)) | ((d_kn_r >= 0.82) & (d_kn_r <= 0.96))
    panel_lines |= ((d_kn_l >= 0.96) & (d_kn_l <= 1.08)) | ((d_kn_r >= 0.96) & (d_kn_r <= 1.08))

    # C. Lames tibiales avant aérodynamiques fuselées (Y: 765..945)
    for yi in range(765, 945):
        t = (yi - 765) / (945 - 765)
        hw_tibia = 28.0 * np.sin(t * np.pi * 0.85 + 0.15)**0.75
        mask_chrome[yi, int(830-hw_tibia):int(830+hw_tibia)] = True
        mask_chrome[yi, int(194-hw_tibia):int(194+hw_tibia)] = True
        # Crête tibiale saillante avec galbe
        height_map[yi, int(830-hw_tibia):int(830+hw_tibia)] += 0.38
        height_map[yi, 829:832] += 0.14
        height_map[yi, 193:196] += 0.14

    # D. Carapaces de mollets galbées en amande (Y: 770..925)
    for yi in range(770, 925):
        t = (yi - 770) / (925 - 770)
        hw_calf = 42.0 * np.sin(t * np.pi)**0.75
        mask_chrome[yi, int(672-hw_calf):int(672+hw_calf)] = True
        mask_chrome[yi, int(352-hw_calf):int(352+hw_calf)] = True
        height_map[yi, int(672-hw_calf):int(672+hw_calf)] += 0.42
        height_map[yi, int(352-hw_calf):int(352+hw_calf)] += 0.42

    print("=== 7. Arrondi Morphologique des Bords (Suppression de Tout Angle Carré) ===")
    # Restriction stricte au maillage réel
    mask_chrome &= is_uv_mesh
    
    # Adoucissement morphologique global : filtre gaussien 3.0 px et seuillage
    raw_mask_img = Image.fromarray((mask_chrome * 255).astype(np.uint8), mode='L')
    filleted_mask = np.array(raw_mask_img.filter(ImageFilter.GaussianBlur(radius=3.0)), dtype=np.float32) / 255.0
    mask_chrome = (filleted_mask >= 0.45) & is_uv_mesh
    
    # Exclusion des pieds et mains
    is_protected = np.zeros((h, w), dtype=bool)
    is_protected[710:1024, 220:805] = True
    mask_chrome &= (~is_protected)
    height_map *= mask_chrome

    # Anti-aliasing des bords de carrosserie
    smooth_alpha = np.array(Image.fromarray((mask_chrome * 255).astype(np.uint8)).filter(ImageFilter.GaussianBlur(radius=1.8)), dtype=np.float32) / 255.0

    print(f"Total pixels de plaques chromées aux courbes pures 360°: {np.count_nonzero(mask_chrome)}")

    print("=== 8. Rendu Métallique Chrome Miroir Sorayama (Éclairage Studio) ===")
    # Normales 3D de surface
    dy, dx = np.gradient(height_map * 24.0)
    nz = 1.0
    norm = np.sqrt(dx**2 + dy**2 + nz**2)
    nx, ny, nz = -dx / norm, -dy / norm, nz / norm

    # Lumière Studio Sorayama
    lx1, ly1, lz1 = 0.12, -0.68, 0.72
    len1 = np.sqrt(lx1**2 + ly1**2 + lz1**2)
    lx1, ly1, lz1 = lx1/len1, ly1/len1, lz1/len1

    lx2, ly2, lz2 = -0.55, 0.25, 0.79
    len2 = np.sqrt(lx2**2 + ly2**2 + lz2**2)
    lx2, ly2, lz2 = lx2/len2, ly2/len2, lz2/len2

    dot1 = np.maximum(0.0, nx*lx1 + ny*ly1 + nz*lz1)
    dot2 = np.maximum(0.0, nx*lx2 + ny*ly2 + nz*lz2)

    # Spéculaire miroir chrome aiguisé et nappe satinée
    hx1, hy1, hz1 = lx1, ly1, lz1 + 1.0
    hlen1 = np.sqrt(hx1**2 + hy1**2 + hz1**2)
    hx1, hy1, hz1 = hx1/hlen1, hy1/hlen1, hz1/hlen1
    dot_h1 = np.maximum(0.0, nx*hx1 + ny*hy1 + nz*hz1)
    spec_sharp = dot_h1 ** 28.0
    spec_soft = dot_h1 ** 7.0

    # Teinte Chrome Argent Miroir Sorayama
    chrome_r = 196.0 + 36.0 * dot1 + 14.0 * dot2 + 96.0 * spec_sharp + 28.0 * spec_soft
    chrome_g = 208.0 + 33.0 * dot1 + 16.0 * dot2 + 96.0 * spec_sharp + 30.0 * spec_soft
    chrome_b = 226.0 + 26.0 * dot1 + 20.0 * dot2 + 96.0 * spec_sharp + 32.0 * spec_soft

    chrome_r = np.clip(chrome_r, 0, 255)
    chrome_g = np.clip(chrome_g, 0, 255)
    chrome_b = np.clip(chrome_b, 0, 255)

    # Assemblage sur le châssis sombre
    out_arr = dark_suit.copy()
    for c in range(3):
        color_c = [chrome_r, chrome_g, chrome_b][c]
        out_arr[:, :, c] = out_arr[:, :, c] * (1.0 - smooth_alpha) + color_c * smooth_alpha

    # Rainures de séparation noires douces (Panel lines mécatroniques)
    edge_dil = np.array(Image.fromarray((mask_chrome * 255).astype(np.uint8)).filter(ImageFilter.MaxFilter(size=3)), dtype=np.uint8) > 0
    groove_mask = (edge_dil & (~mask_chrome) & is_uv_mesh & (~is_protected)) | panel_lines
    out_arr[groove_mask, 0] = np.minimum(out_arr[groove_mask, 0], 10.0)
    out_arr[groove_mask, 1] = np.minimum(out_arr[groove_mask, 1], 14.0)
    out_arr[groove_mask, 2] = np.minimum(out_arr[groove_mask, 2], 22.0)

    # Liserés néon cyan fins (#00f5d4)
    neon_final = neon_lines & mask_chrome & (~is_protected)
    out_arr[neon_final, 0] = 0.0
    out_arr[neon_final, 1] = 245.0
    out_arr[neon_final, 2] = 212.0

    # Mains et ongles préservés
    out_arr[is_protected] = cur_arr[is_protected]

    # Transparence hors UV
    out_arr[~is_uv_mesh, 3] = 0.0

    final_img = Image.fromarray(out_arr.astype(np.uint8), mode='RGBA')
    final_img.save('packages/compagnon-desktop/overlay/vrm/body_skin_android.png')
    final_img.save('packages/cortex/compagnon_ui/public/vrm/body_skin_android.png')
    print("=== Texture Sorayama Curves Master 360° générée avec succès ! ===")

if __name__ == '__main__':
    generate_sorayama_curved_master()
