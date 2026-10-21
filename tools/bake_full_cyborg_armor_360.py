import numpy as np
from PIL import Image, ImageFilter

def generate_cyborg_armor_master():
    print("=== 1. Initialisation des textures et gabarit UV ===")
    h, w = 1024, 1024

    # Gabarit UV vert pour contraindre 100% de la carrosserie au maillage réel
    green_im = Image.open('/home/lbg/.gemini/antigravity-ide/brain/1165e65b-2952-49ad-8ee9-8135d868d941/.user_uploaded/media_1792613031209.png')
    green_arr = np.array(green_im)
    is_uv_mesh = (green_arr[:, :, 1] > 50) & (green_arr[:, :, 0] < 50) & (green_arr[:, :, 2] < 50)

    # Récupération des mains, phalanges et ongles
    cur_img = Image.open('packages/compagnon-desktop/overlay/vrm/body_skin_android.png').convert('RGBA')
    cur_arr = np.array(cur_img, dtype=np.float32)

    y_idx, x_idx = np.ogrid[:h, :w]

    # Sous-châssis sombre mécatronique (Anthracite bleuté texturé en kevlar/fibres)
    dark_suit = np.zeros((h, w, 4), dtype=np.float32)
    dark_suit[:, :, 0] = 16.0
    dark_suit[:, :, 1] = 22.0
    dark_suit[:, :, 2] = 32.0
    dark_suit[:, :, 3] = 255.0

    # Nervures de câbles musculaires / fibres synthétiques dans les creux
    fiber = np.sin((x_idx + y_idx * 0.45) * 0.4) * 4.0 + np.sin((y_idx - x_idx * 0.3) * 0.55) * 3.0
    dark_suit[:, :, 0] += fiber
    dark_suit[:, :, 1] += fiber * 1.15
    dark_suit[:, :, 2] += fiber * 1.4

    # Initialisation des masques
    mask_chrome = np.zeros((h, w), dtype=bool)
    height_map = np.zeros((h, w), dtype=np.float32)
    panel_lines = np.zeros((h, w), dtype=bool)
    neon_lines = np.zeros((h, w), dtype=bool)

    print("=== 2. Sculpture du Bustier Central Continu (Bodie Mecha façon Image 4 & 5) ===")
    # A. Col montant / Gorge (Y: 100..165)
    for yi in range(105, 165):
        t = (yi - 105) / (165 - 105)
        hw_neck = 28.0 + 16.0 * t
        mask_chrome[yi, int(512-hw_neck):int(512+hw_neck)] = True
        height_map[yi, int(512-hw_neck):int(512+hw_neck)] += 0.35

    # B. Dômes de Poitrine Galbés Voluptueux (Centres X=449 et X=575, Y=255)
    r_x, r_y = 74.0, 70.0
    d_l = np.sqrt(((x_idx - 575.0) / r_x)**2 + ((y_idx - 255.0) / r_y)**2)
    d_r = np.sqrt(((x_idx - 449.0) / r_x)**2 + ((y_idx - 255.0) / r_y)**2)
    is_breast = (d_l <= 1.0) | (d_r <= 1.0)
    mask_chrome |= is_breast

    h_breast_l = np.sqrt(np.maximum(0.0, 1.0 - d_l**2)) * (d_l <= 1.0)
    h_breast_r = np.sqrt(np.maximum(0.0, 1.0 - d_r**2)) * (d_r <= 1.0)
    height_map += (h_breast_l + h_breast_r) * 0.68

    # Plastron central sternal réunissant les seins d'un seul tenant (Y: 165..280)
    for yi in range(165, 280):
        t = (yi - 165) / (280 - 165)
        hw_st = 44.0 + 35.0 * np.sin(t * np.pi * 0.6)
        mask_chrome[yi, int(512-hw_st):int(512+hw_st)] = True
        height_map[yi, int(512-hw_st):int(512+hw_st)] += 0.40

    # C. Arceau rigide sous-mammaire (Pli continu sous les seins)
    for xi in range(370, 655):
        y_arch = int(308.0 + 14.0 * np.cos((xi - 512.0) / 140.0 * np.pi * 0.5))
        mask_chrome[y_arch-4:y_arch+5, xi] = True
        height_map[y_arch-4:y_arch+5, xi] += 0.42
        panel_lines[y_arch+5:y_arch+7, xi] = True

    # D. Abdomen en 5 tablettes de blindage mécatroniques sculptées (Y: 320..495)
    # Silhouette galbée en sablier (large sous seins, svelte à la taille, évasée aux hanches)
    abdo_levels = [320, 355, 390, 425, 460, 495]
    for yi in range(320, 495):
        t = (yi - 320) / (495 - 320)
        # S-curve galbée
        s_curve = 50.0 + 38.0 * (1.0 - np.sin(t * np.pi))**1.3 + 12.0 * t
        mask_chrome[yi, int(512-s_curve):int(512+s_curve)] = True

        # Galbe bombé abdominal
        dx_val = np.abs(x_idx[0, int(512-s_curve):int(512+s_curve)] - 512.0) / s_curve
        height_map[yi, int(512-s_curve):int(512+s_curve)] += (1.0 - dx_val**2) * 0.48

        # Fentes de séparation des 5 tablettes mécatroniques
        if any(abs(yi - lvl) <= 1 for lvl in abdo_levels[1:-1]):
            panel_lines[yi, int(512-s_curve+6):int(512+s_curve-6)] = True

        # Lignes néon cyan verticales le long des flancs du bustier (exactement comme Image 4 !)
        neon_lines[yi, int(512-s_curve):int(512-s_curve+3)] = True
        neon_lines[yi, int(512+s_curve-3):int(512+s_curve)] = True

    # E. Coque pelvienne haute (High-cut mecha leotard) & Entrejambe en pointe (Y: 495..588)
    for yi in range(495, 588):
        t = (yi - 495) / (588 - 495)
        hw_pelvis = 75.0 * (1.0 - t**0.9)
        mask_chrome[yi, int(512-hw_pelvis):int(512+hw_pelvis)] = True
        height_map[yi, int(512-hw_pelvis):int(512+hw_pelvis)] += 0.45 * (1.0 - t * 0.4)
        if hw_pelvis >= 3.0:
            neon_lines[yi, int(512-hw_pelvis):int(512-hw_pelvis+2)] = True
            neon_lines[yi, int(512+hw_pelvis-2):int(512+hw_pelvis)] = True

    print("=== 3. Grosses Rotules Circulaires Mécaniques de Hanches (Hip Pivots) ===")
    # C'est la signature cyborg des images 4 et 5 !
    # Deux pivots circulaires majestueux sur les têtes de fémurs
    d_hip_l = np.sqrt(((x_idx - 622.0) / 32.0)**2 + ((y_idx - 530.0) / 32.0)**2)
    d_hip_r = np.sqrt(((x_idx - 402.0) / 32.0)**2 + ((y_idx - 530.0) / 32.0)**2)
    is_hip_pivot = (d_hip_l <= 1.0) | (d_hip_r <= 1.0)
    mask_chrome |= is_hip_pivot
    h_pivot_l = np.sqrt(np.maximum(0.0, 1.0 - d_hip_l**2)) * (d_hip_l <= 1.0)
    h_pivot_r = np.sqrt(np.maximum(0.0, 1.0 - d_hip_r**2)) * (d_hip_r <= 1.0)
    height_map += (h_pivot_l + h_pivot_r) * 0.55
    # Anneau de gorge circulaire noir & anneau néon
    panel_lines |= ((d_hip_l >= 0.70) & (d_hip_l <= 0.82)) | ((d_hip_r >= 0.70) & (d_hip_r <= 0.82))
    neon_lines |= ((d_hip_l >= 0.82) & (d_hip_l <= 0.94)) | ((d_hip_r >= 0.82) & (d_hip_r <= 0.94))

    print("=== 4. Sculpture des Cuisses Enveloppantes & Genoux Articulés (Jambes) ===")
    # A. Grandes plaques fémorales enveloppantes (Couvrent 70% de la cuisse avec panel lines)
    # Y in [520..675]
    for yi in range(520, 675):
        t = (yi - 520) / (675 - 520)
        hw_thigh = 62.0 * np.sin(t * np.pi)**0.65
        mask_chrome[yi, int(842-hw_thigh):int(842+hw_thigh)] = True
        mask_chrome[yi, int(182-hw_thigh):int(182+hw_thigh)] = True
        
        # Galbe musculaire puissant du quadriceps
        dx_th = np.abs(x_idx[0, int(842-hw_thigh):int(842+hw_thigh)] - 842.0) / (hw_thigh + 1e-5)
        height_map[yi, int(842-hw_thigh):int(842+hw_thigh)] += (1.0 - dx_th**2) * 0.50
        dx_th_r = np.abs(x_idx[0, int(182-hw_thigh):int(182+hw_thigh)] - 182.0) / (hw_thigh + 1e-5)
        height_map[yi, int(182-hw_thigh):int(182+hw_thigh)] += (1.0 - dx_th_r**2) * 0.50

        # Rainure de découpe aérodynamique le long de la cuisse (façon Robocop / Image 5)
        pos_line_l = int(842 + hw_thigh * 0.55)
        pos_line_r = int(182 - hw_thigh * 0.55)
        panel_lines[yi, pos_line_l:pos_line_l+2] = True
        panel_lines[yi, pos_line_r-2:pos_line_r] = True

    # B. Rotules de Genoux Mécatroniques Circulaires (Y: 692..752)
    d_kn_l = np.sqrt(((x_idx - 846.0) / 32.0)**2 + ((y_idx - 722.0) / 28.0)**2)
    d_kn_r = np.sqrt(((x_idx - 178.0) / 32.0)**2 + ((y_idx - 722.0) / 28.0)**2)
    is_knee = (d_kn_l <= 1.0) | (d_kn_r <= 1.0)
    mask_chrome |= is_knee
    height_map += (np.sqrt(np.maximum(0.0, 1.0 - d_kn_l**2)) * (d_kn_l <= 1.0) + np.sqrt(np.maximum(0.0, 1.0 - d_kn_r**2)) * (d_kn_r <= 1.0)) * 0.55
    # Gorge d'ombre & anneau néon
    panel_lines |= ((d_kn_l >= 0.72) & (d_kn_l <= 0.84)) | ((d_kn_r >= 0.72) & (d_kn_r <= 0.84))
    neon_lines |= ((d_kn_l >= 0.84) & (d_kn_l <= 0.96)) | ((d_kn_r >= 0.84) & (d_kn_r <= 0.96))

    # C. Armure Tibiale Enveloppante avec Biseau Saillant (Y: 765..950)
    for yi in range(765, 950):
        t = (yi - 765) / (950 - 765)
        hw_tibia = 40.0 * np.sin(t * np.pi * 0.85 + 0.15)**0.7
        mask_chrome[yi, int(830-hw_tibia):int(830+hw_tibia)] = True
        mask_chrome[yi, int(194-hw_tibia):int(194+hw_tibia)] = True
        height_map[yi, int(830-hw_tibia):int(830+hw_tibia)] += 0.42
        # Arête centrale saillante
        height_map[yi, 829:832] += 0.18
        height_map[yi, 193:196] += 0.18

    # D. Carrosserie Galbée des Mollets Arrière (Y: 770..930)
    for yi in range(770, 930):
        t = (yi - 770) / (930 - 770)
        hw_calf = 52.0 * np.sin(t * np.pi)**0.75
        mask_chrome[yi, int(672-hw_calf):int(672+hw_calf)] = True
        mask_chrome[yi, int(352-hw_calf):int(352+hw_calf)] = True
        height_map[yi, int(672-hw_calf):int(672+hw_calf)] += 0.45
        height_map[yi, int(352-hw_calf):int(352+hw_calf)] += 0.45

    print("=== 5. Sculpture des Épaules, Biceps & Avant-bras ===")
    # A. Coques d'épaulettes carénées profilées (Y: 35..110)
    d_sh_l = np.sqrt(((x_idx - 912.0) / 48.0)**2 + ((y_idx - 72.0) / 38.0)**2)
    d_sh_r = np.sqrt(((x_idx - 112.0) / 48.0)**2 + ((y_idx - 72.0) / 38.0)**2)
    is_shoulder = (d_sh_l <= 1.0) | (d_sh_r <= 1.0)
    mask_chrome |= is_shoulder
    height_map += (np.sqrt(np.maximum(0.0, 1.0 - d_sh_l**2)) * (d_sh_l <= 1.0) + np.sqrt(np.maximum(0.0, 1.0 - d_sh_r**2)) * (d_sh_r <= 1.0)) * 0.45
    neon_lines |= ((d_sh_l >= 0.88) & (d_sh_l <= 0.98)) | ((d_sh_r >= 0.88) & (d_sh_r <= 0.98))

    # B. Brassards de Biceps enveloppants (Y: 112..228)
    for yi in range(112, 228):
        t = (yi - 112) / (228 - 112)
        hw_arm = 48.0 * np.sin(t * np.pi)**0.72
        mask_chrome[yi, int(910-hw_arm):int(910+hw_arm)] = True
        mask_chrome[yi, int(114-hw_arm):int(114+hw_arm)] = True
        height_map[yi, int(910-hw_arm):int(910+hw_arm)] += 0.40
        height_map[yi, int(114-hw_arm):int(114+hw_arm)] += 0.40
        # Rainure latérale
        pos_line_arm_l = int(910 + hw_arm * 0.5)
        pos_line_arm_r = int(114 - hw_arm * 0.5)
        panel_lines[yi, pos_line_arm_l:pos_line_arm_l+2] = True
        panel_lines[yi, pos_line_arm_r-2:pos_line_arm_r] = True

    # C. Rotules circulaires de coudes (Y: 234..278)
    d_elb_l = np.sqrt(((x_idx - 910.0) / 26.0)**2 + ((y_idx - 256.0) / 22.0)**2)
    d_elb_r = np.sqrt(((x_idx - 114.0) / 26.0)**2 + ((y_idx - 256.0) / 22.0)**2)
    is_elbow = (d_elb_l <= 1.0) | (d_elb_r <= 1.0)
    mask_chrome |= is_elbow
    height_map += (np.maximum(0.0, 1.0 - d_elb_l) * (d_elb_l <= 1.0) + np.maximum(0.0, 1.0 - d_elb_r) * (d_elb_r <= 1.0)) * 0.45
    panel_lines |= ((d_elb_l >= 0.88) & (d_elb_l <= 1.02)) | ((d_elb_r >= 0.88) & (d_elb_r <= 1.02))

    # D. Avant-bras fuselés en gantelets protecteurs (Y: 288..438)
    for yi in range(288, 438):
        t = (yi - 288) / (438 - 288)
        hw_fa = 44.0 * np.sin(t * np.pi * 0.9 + 0.1)**0.72
        mask_chrome[yi, int(908-hw_fa):int(908+hw_fa)] = True
        mask_chrome[yi, int(116-hw_fa):int(116+hw_fa)] = True
        height_map[yi, int(908-hw_fa):int(908+hw_fa)] += 0.40
        height_map[yi, int(116-hw_fa):int(116+hw_fa)] += 0.40

    print("=== 6. Sculpture du Dos 360° (Carapace Scapulaire, Colonne & Fessiers) ===")
    # A. Grandes Carapaces Scapulaires (Omoplates galbées continues, Y: 165..315)
    for yi in range(165, 315):
        t = (yi - 165) / (315 - 165)
        w_scap = 65.0 * np.sin(t * np.pi)**0.75
        cx_scap_r, cx_scap_l = 312.0, 712.0
        mask_chrome[yi, int(cx_scap_r-w_scap):int(cx_scap_r+w_scap)] = True
        mask_chrome[yi, int(cx_scap_l-w_scap):int(cx_scap_l+w_scap)] = True
        height_map[yi, int(cx_scap_r-w_scap):int(cx_scap_r+w_scap)] += 0.42
        height_map[yi, int(cx_scap_l-w_scap):int(cx_scap_l+w_scap)] += 0.42

    # B. Colonne Vertébrale Exosquelette Mécanique (Modules vertébraux titane, Y: 165..485)
    for yi in range(165, 485):
        t_mod = (yi % 22) / 22.0
        rad_vert = 16.0 * np.sin(t_mod * np.pi)
        if rad_vert > 1.0:
            mask_chrome[yi, int(260-rad_vert):int(260+rad_vert)] = True
            mask_chrome[yi, int(764-rad_vert):int(764+rad_vert)] = True
            height_map[yi, int(260-rad_vert):int(260+rad_vert)] += 0.50
            height_map[yi, int(764-rad_vert):int(764+rad_vert)] += 0.50
        
        # Disques intervertébraux noirs d'amortissement
        if yi % 22 in [0, 1, 21]:
            panel_lines[yi, 245:276] = True
            panel_lines[yi, 748:779] = True
        
        # Diodes neurales cyan au centre de chaque vertèbre
        if yi % 22 in [9, 10, 11, 12]:
            neon_lines[yi, 259:262] = True
            neon_lines[yi, 763:766] = True

    # C. Double Coque Galbée d'Armure Fessière (Dômes voluptueux Y: 505..645)
    d_butt_r = np.sqrt(((x_idx - 306.0) / 58.0)**2 + ((y_idx - 575.0) / 62.0)**2)
    d_butt_l = np.sqrt(((x_idx - 718.0) / 58.0)**2 + ((y_idx - 575.0) / 62.0)**2)
    is_buttock = (d_butt_r <= 1.0) | (d_butt_l <= 1.0)
    mask_chrome |= is_buttock
    h_butt_r = np.sqrt(np.maximum(0.0, 1.0 - d_butt_r**2)) * (d_butt_r <= 1.0)
    h_butt_l = np.sqrt(np.maximum(0.0, 1.0 - d_butt_l**2)) * (d_butt_l <= 1.0)
    height_map += (h_butt_r + h_butt_l) * 0.62

    # Sillon inter-fessier net
    panel_lines[505:640, 246:252] = True
    panel_lines[505:640, 772:778] = True

    print("=== 7. Arrondi Morphologique Global (Fillet Rayon 3.5 px) ===")
    mask_chrome &= is_uv_mesh

    # Fillet morphologique : élimination absolue de tout angle aigu ou coupe carrée
    raw_mask_img = Image.fromarray((mask_chrome * 255).astype(np.uint8), mode='L')
    filleted_mask = np.array(raw_mask_img.filter(ImageFilter.GaussianBlur(radius=3.5)), dtype=np.float32) / 255.0
    mask_chrome = (filleted_mask >= 0.42) & is_uv_mesh

    # Protection stricte des ongles et pieds originaux
    is_protected = np.zeros((h, w), dtype=bool)
    is_protected[710:1024, 220:805] = True
    mask_chrome &= (~is_protected)
    height_map *= mask_chrome

    smooth_alpha = np.array(Image.fromarray((mask_chrome * 255).astype(np.uint8)).filter(ImageFilter.GaussianBlur(radius=2.0)), dtype=np.float32) / 255.0

    print(f"Total pixels de carrosserie cyborg enveloppante active: {np.count_nonzero(mask_chrome)} ({np.count_nonzero(mask_chrome)/np.count_nonzero(is_uv_mesh)*100:.1f}% du corps)")

    print("=== 8. Éclairage Studio Chrome Liquide Sorayama & Matériaux ===")
    dy, dx = np.gradient(height_map * 26.0)
    nz = 1.0
    norm = np.sqrt(dx**2 + dy**2 + nz**2)
    nx, ny, nz = -dx / norm, -dy / norm, nz / norm

    # Double éclairage studio haute brillance
    lx1, ly1, lz1 = 0.14, -0.70, 0.70
    len1 = np.sqrt(lx1**2 + ly1**2 + lz1**2)
    lx1, ly1, lz1 = lx1/len1, ly1/len1, lz1/len1

    lx2, ly2, lz2 = -0.58, 0.22, 0.78
    len2 = np.sqrt(lx2**2 + ly2**2 + lz2**2)
    lx2, ly2, lz2 = lx2/len2, ly2/len2, lz2/len2

    dot1 = np.maximum(0.0, nx*lx1 + ny*ly1 + nz*lz1)
    dot2 = np.maximum(0.0, nx*lx2 + ny*ly2 + nz*lz2)

    hx1, hy1, hz1 = lx1, ly1, lz1 + 1.0
    hlen1 = np.sqrt(hx1**2 + hy1**2 + hz1**2)
    hx1, hy1, hz1 = hx1/hlen1, hy1/hlen1, hz1/hlen1
    dot_h1 = np.maximum(0.0, nx*hx1 + ny*hy1 + nz*hz1)
    spec_sharp = dot_h1 ** 30.0
    spec_soft = dot_h1 ** 8.0

    # Chrome Argenté Miroir Liquide Pur (Reflets vifs très riches)
    chrome_r = 198.0 + 36.0 * dot1 + 14.0 * dot2 + 98.0 * spec_sharp + 26.0 * spec_soft
    chrome_g = 210.0 + 33.0 * dot1 + 16.0 * dot2 + 98.0 * spec_sharp + 28.0 * spec_soft
    chrome_b = 228.0 + 26.0 * dot1 + 20.0 * dot2 + 98.0 * spec_sharp + 30.0 * spec_soft

    chrome_r = np.clip(chrome_r, 0, 255)
    chrome_g = np.clip(chrome_g, 0, 255)
    chrome_b = np.clip(chrome_b, 0, 255)

    # Assemblage sur le châssis sombre
    out_arr = dark_suit.copy()
    for c in range(3):
        color_c = [chrome_r, chrome_g, chrome_b][c]
        out_arr[:, :, c] = out_arr[:, :, c] * (1.0 - smooth_alpha) + color_c * smooth_alpha

    # Rainures de découpe noires d'occlusion ambiante (Panel lines industrielles fines)
    edge_dil = np.array(Image.fromarray((mask_chrome * 255).astype(np.uint8)).filter(ImageFilter.MaxFilter(size=3)), dtype=np.uint8) > 0
    groove_mask = (edge_dil & (~mask_chrome) & is_uv_mesh & (~is_protected)) | panel_lines
    out_arr[groove_mask, 0] = np.minimum(out_arr[groove_mask, 0], 8.0)
    out_arr[groove_mask, 1] = np.minimum(out_arr[groove_mask, 1], 12.0)
    out_arr[groove_mask, 2] = np.minimum(out_arr[groove_mask, 2], 18.0)

    # Liserés néon cyan luminescents de précision (#00f5d4)
    neon_final = neon_lines & mask_chrome & (~is_protected)
    out_arr[neon_final, 0] = 0.0
    out_arr[neon_final, 1] = 245.0
    out_arr[neon_final, 2] = 212.0

    # Réinjection des ongles et mains
    out_arr[is_protected] = cur_arr[is_protected]

    # Masquage transparent hors maillage
    out_arr[~is_uv_mesh, 3] = 0.0

    final_img = Image.fromarray(out_arr.astype(np.uint8), mode='RGBA')
    final_img.save('packages/compagnon-desktop/overlay/vrm/body_skin_android.png')
    final_img.save('packages/cortex/compagnon_ui/public/vrm/body_skin_android.png')
    print("=== Texture Full Cyborg Armor 360° générée avec succès ! ===")

if __name__ == '__main__':
    generate_cyborg_armor_master()
