import numpy as np
from PIL import Image, ImageFilter, ImageDraw

def generate_sorayama_360():
    print("--- 1. Initialisation des textures et dimensions ---")
    h, w = 1024, 1024
    
    # Charger l'image du template vert pour contraindre 100% des éléments à la surface UV réelle
    green_im = Image.open('/home/lbg/.gemini/antigravity-ide/brain/1165e65b-2952-49ad-8ee9-8135d868d941/.user_uploaded/media_1792613031209.png')
    green_arr = np.array(green_im)
    is_uv_mesh = (green_arr[:, :, 1] > 50) & (green_arr[:, :, 0] < 50) & (green_arr[:, :, 2] < 50)

    # Image courante pour les mains et ongles
    cur_img = Image.open('packages/compagnon-desktop/overlay/vrm/body_skin_android.png').convert('RGBA')
    cur_arr = np.array(cur_img, dtype=np.float32)

    # 1. Base châssis sombre mécatronique Sorayama (Anthracite profond avec striures de fibres de carbone)
    # Fond sombre subtilement bleuté #121824
    dark_suit = np.zeros((h, w, 4), dtype=np.float32)
    dark_suit[:, :, 0] = 18.0
    dark_suit[:, :, 1] = 24.0
    dark_suit[:, :, 2] = 36.0
    dark_suit[:, :, 3] = 255.0

    # Striures de câbles musculaires / fibres synthétiques dans les creux
    y_idx, x_idx = np.ogrid[:h, :w]
    fiber_pattern = np.sin((x_idx + y_idx * 0.5) * 0.4) * 4.0 + np.sin((y_idx - x_idx * 0.3) * 0.6) * 3.0
    dark_suit[:, :, 0] += fiber_pattern
    dark_suit[:, :, 1] += fiber_pattern * 1.2
    dark_suit[:, :, 2] += fiber_pattern * 1.5

    # 2. Masque complet des plaques chromées Sorayama (Face ET Dos 360°)
    mask_chrome = np.zeros((h, w), dtype=bool)
    height_map = np.zeros((h, w), dtype=np.float32)
    panel_lines = np.zeros((h, w), dtype=bool)
    neon_lines = np.zeros((h, w), dtype=bool)

    print("--- 2. Sculpture des plaques Torse, Poitrine & Dos (360°) ---")
    # A. Dômes de Poitrine Sorayama (Seins sphériques parfaits)
    # Centres: gauche=(575, 255), droite=(449, 255), rayon=68 px
    d_l = np.sqrt((x_idx - 575.0)**2 + (y_idx - 255.0)**2)
    d_r = np.sqrt((x_idx - 449.0)**2 + (y_idx - 255.0)**2)
    r_breast = 68.0
    is_breast = (d_l <= r_breast) | (d_r <= r_breast)
    mask_chrome |= is_breast

    # Galbe sphérique franc Sorayama
    h_breast_l = np.sqrt(np.maximum(0.0, 1.0 - (d_l / r_breast)**2)) * (d_l <= r_breast)
    h_breast_r = np.sqrt(np.maximum(0.0, 1.0 - (d_r / r_breast)**2)) * (d_r <= r_breast)
    height_map += (h_breast_l + h_breast_r) * 0.65

    # Liseré néon discret sur la bordure extérieure des dômes
    neon_lines |= ((d_l >= 63.0) & (d_l <= 66.0)) | ((d_r >= 63.0) & (d_r <= 66.0))

    # B. Plastron central sternum & clavicules (Haut torse avant)
    # Épouse le haut de Y=160 à Y=280
    is_sternum = (x_idx >= 465) & (x_idx <= 559) & (y_idx >= 160) & (y_idx <= 280)
    mask_chrome |= is_sternum
    height_map += 0.35 * is_sternum

    # C. Arceau rigide sous-mammaire (Séparation poitrine / abdomen)
    for y in range(305, 318):
        mask_chrome[y, 380:644] = True
        height_map[y, 380:644] += 0.40
    panel_lines[318:320, 380:644] = True

    # D. Abdomen fuselé Sorayama (Carrosserie cambrée avec fentes aérodynamiques)
    # Largeur fluide s'effilant de 140 px sous les seins à 90 px au nombril
    for y in range(320, 490):
        prog = (y - 320) / (490 - 320)
        half_w = int(70 * (1.0 - 0.32 * np.sin(prog * np.pi * 0.9)))
        mask_chrome[y, 512-half_w:512+half_w] = True
        # Galbe bombé abdominal central
        d_x = np.abs(x_idx[0, 512-half_w:512+half_w] - 512.0) / half_w
        height_map[y, 512-half_w:512+half_w] += (1.0 - d_x**2) * 0.45

        # Lignes de séparation segmentaires horizontales mécatroniques (3 anneaux abdo)
        if y in [360, 405, 450]:
            panel_lines[y:y+2, 512-half_w:512+half_w] = True

    # E. Coque Pelvienne en V Sorayama & Carénage de Hanche
    for y in range(492, 580):
        prog = (y - 492) / (580 - 492)
        half_w = int(58 * (1.0 - 0.75 * prog))
        mask_chrome[y, 512-half_w:512+half_w] = True
        height_map[y, 512-half_w:512+half_w] += 0.40

    # Liseré néon en V sur le pelvis
    for y in range(496, 574):
        prog = (y - 492) / (580 - 492)
        half_w = int(58 * (1.0 - 0.75 * prog))
        neon_lines[y, 512-half_w:512-half_w+2] = True
        neon_lines[y, 512+half_w-2:512+half_w] = True

    # F. Carapaces de Hanches latérales hautes
    for y in range(500, 560):
        mask_chrome[y, 385:435] = True
        mask_chrome[y, 589:639] = True
        height_map[y, 385:435] += 0.30
        height_map[y, 589:639] += 0.30

    # --- G. DOS COMPLET 360° (Scapula, Colonne Vertébrale, Fessiers) ---
    # Dans l'UV VRoid, les ailes latérales de l'îlot Torse (X: 245..380 et 644..776) forment le DOS !
    # 1. Omoplates galbées (Scapula) en haut du dos (Y: 160..310)
    for y in range(170, 310):
        mask_chrome[y, 255:365] = True
        mask_chrome[y, 659:769] = True
        # Galbe bombé des omoplates
        height_map[y, 255:365] += 0.38
        height_map[y, 659:769] += 0.38

    # 2. Colonne vertébrale mécatronique articulée Sorayama (le long de la couture dorsale 250 <-> 774)
    # Série de modules vertébraux chromés de Y=160 à Y=480
    for y in range(170, 480):
        # Largeur de la colonne vertébrale
        mask_chrome[y, 246:275] = True
        mask_chrome[y, 749:778] = True
        height_map[y, 246:275] += 0.45
        height_map[y, 749:778] += 0.45
        
        # Disques intervertébraux noirs tous les 24 px
        if y % 24 in [0, 1, 2]:
            panel_lines[y, 246:275] = True
            panel_lines[y, 749:778] = True
        
        # Canal neural cyan central
        if y % 24 in [10, 11, 12, 13]:
            neon_lines[y, 258:262] = True
            neon_lines[y, 762:766] = True

    # 3. Double Coque Galbée des Fessiers (Y: 510..640 sur le dos)
    # Deux dômes fessiers chromés somptueux
    d_butt_r = np.sqrt(((x_idx - 305.0) / 45.0)**2 + ((y_idx - 575.0) / 50.0)**2)
    d_butt_l = np.sqrt(((x_idx - 719.0) / 45.0)**2 + ((y_idx - 575.0) / 50.0)**2)
    is_buttock = (d_butt_r <= 1.0) | (d_butt_l <= 1.0)
    mask_chrome |= is_buttock
    h_butt_r = np.sqrt(np.maximum(0.0, 1.0 - d_butt_r**2)) * (d_butt_r <= 1.0)
    h_butt_l = np.sqrt(np.maximum(0.0, 1.0 - d_butt_l**2)) * (d_butt_l <= 1.0)
    height_map += (h_butt_r + h_butt_l) * 0.55

    print("--- 3. Sculpture des Bras & Épaules (Sorayama) ---")
    # A. Épaulettes deltoïdes (Haut des bras, Y: 40..110)
    for y in range(40, 110):
        mask_chrome[y, 865:960] = True
        mask_chrome[y, 64:159] = True
        height_map[y, 865:960] += 0.35
        height_map[y, 64:159] += 0.35

    # B. Biceps / Face externe du bras (Y: 115..220)
    for y in range(115, 220):
        mask_chrome[y, 870:950] = True
        mask_chrome[y, 74:154] = True
        # Galbe cylindrique
        dx_b_l = np.abs(x_idx[0, 870:950] - 910.0) / 40.0
        dx_b_r = np.abs(x_idx[0, 74:154] - 114.0) / 40.0
        height_map[y, 870:950] += (1.0 - dx_b_l**2) * 0.40
        height_map[y, 74:154] += (1.0 - dx_b_r**2) * 0.40

    # C. Rotule de Coude mécatronique circulaire (Y: 235..275)
    d_elb_l = np.sqrt(((x_idx - 910.0) / 22.0)**2 + ((y_idx - 255.0) / 18.0)**2)
    d_elb_r = np.sqrt(((x_idx - 114.0) / 22.0)**2 + ((y_idx - 255.0) / 18.0)**2)
    is_elbow = (d_elb_l <= 1.0) | (d_elb_r <= 1.0)
    mask_chrome |= is_elbow
    height_map += (np.maximum(0.0, 1.0 - d_elb_l) * (d_elb_l <= 1.0) + np.maximum(0.0, 1.0 - d_elb_r) * (d_elb_r <= 1.0)) * 0.35

    # D. Avant-bras fuselé Sorayama (Y: 290..430)
    for y in range(290, 430):
        prog = (y - 290) / (430 - 290)
        hw = int(38 * (1.0 - 0.22 * prog))
        mask_chrome[y, 908-hw:908+hw] = True
        mask_chrome[y, 116-hw:116+hw] = True
        height_map[y, 908-hw:908+hw] += 0.35
        height_map[y, 116-hw:116+hw] += 0.35

    print("--- 4. Sculpture des Jambes, Genoux & Mollets (Sorayama) ---")
    # A. Carénage fémoral avant & externe des cuisses (Y: 530..670)
    for y in range(530, 670):
        mask_chrome[y, 800:885] = True
        mask_chrome[y, 139:224] = True
        dx_th_l = np.abs(x_idx[0, 800:885] - 842.0) / 42.0
        dx_th_r = np.abs(x_idx[0, 139:224] - 182.0) / 42.0
        height_map[y, 800:885] += (1.0 - dx_th_l**2) * 0.45
        height_map[y, 139:224] += (1.0 - dx_th_r**2) * 0.45

    # Fente aérodynamique latérale sur la cuisse
    for y in range(560, 640):
        panel_lines[y, 860:862] = True
        panel_lines[y, 162:164] = True

    # B. Rotules de Genoux mécatroniques Sorayama (Y: 695..748)
    d_kn_l = np.sqrt(((x_idx - 846.0) / 26.0)**2 + ((y_idx - 722.0) / 22.0)**2)
    d_kn_r = np.sqrt(((x_idx - 178.0) / 26.0)**2 + ((y_idx - 722.0) / 22.0)**2)
    is_knee = (d_kn_l <= 1.0) | (d_kn_r <= 1.0)
    mask_chrome |= is_knee
    height_map += (np.maximum(0.0, 1.0 - d_kn_l) * (d_kn_l <= 1.0) + np.maximum(0.0, 1.0 - d_kn_r) * (d_kn_r <= 1.0)) * 0.45
    neon_lines |= ((d_kn_l >= 0.78) & (d_kn_l <= 0.95)) | ((d_kn_r >= 0.78) & (d_kn_r <= 0.95))

    # C. Plaques Tibiales avant fuselées (Y: 765..940)
    for y in range(765, 940):
        prog = (y - 765) / (940 - 765)
        hw = int(30 * (1.0 - 0.30 * prog))
        mask_chrome[y, 830-hw:830+hw] = True
        mask_chrome[y, 194-hw:194+hw] = True
        height_map[y, 830-hw:830+hw] += 0.38
        height_map[y, 194-hw:194+hw] += 0.38
        # Crête tibiale saillante
        height_map[y, 829:832] += 0.15
        height_map[y, 193:196] += 0.15

    # D. Carénage des Mollets arrière (Y: 770..920 sur l'extérieur de l'îlot jambe)
    for y in range(770, 920):
        mask_chrome[y, 630:715] = True
        mask_chrome[y, 309:394] = True
        height_map[y, 630:715] += 0.40
        height_map[y, 309:394] += 0.40

    # 5. Restreindre strictement aux îles réelles du maillage UV (supprime tout débordement)
    mask_chrome &= is_uv_mesh
    height_map *= mask_chrome

    # Protection zone pieds, ongles et mains
    is_protected = np.zeros((h, w), dtype=bool)
    is_protected[710:1024, 220:805] = True
    mask_chrome &= (~is_protected)
    height_map *= (~is_protected)

    print(f"Total pixels de plaques chromées 360° actives: {np.count_nonzero(mask_chrome)}")

    # --- 5. Rendu Matériau Chrome Miroir Poli Sorayama ---
    print("--- 5. Calcul de l'éclairage de studio Chrome Liquide ---")
    mask_img = Image.fromarray((mask_chrome * 255).astype(np.uint8), mode='L')
    smooth_mask = np.array(mask_img.filter(ImageFilter.GaussianBlur(radius=1.5)), dtype=np.float32) / 255.0

    # Normales 3D de surface
    dy, dx = np.gradient(height_map * 22.0)
    nz = 1.0
    norm = np.sqrt(dx**2 + dy**2 + nz**2)
    nx, ny, nz = -dx / norm, -dy / norm, nz / norm

    # Lumière Studio Haute Définition Sorayama (Reflet zénithal + Spéculaire pur)
    # Source principale douce
    lx1, ly1, lz1 = 0.15, -0.65, 0.74
    len1 = np.sqrt(lx1**2 + ly1**2 + lz1**2)
    lx1, ly1, lz1 = lx1/len1, ly1/len1, lz1/len1

    # Source secondaire de débouchage latérale
    lx2, ly2, lz2 = -0.60, 0.20, 0.77
    len2 = np.sqrt(lx2**2 + ly2**2 + lz2**2)
    lx2, ly2, lz2 = lx2/len2, ly2/len2, lz2/len2

    dot1 = np.maximum(0.0, nx*lx1 + ny*ly1 + nz*lz1)
    dot2 = np.maximum(0.0, nx*lx2 + ny*ly2 + nz*lz2)

    # Spéculaire ultra-brillant chrome Sorayama
    hx1, hy1, hz1 = lx1, ly1, lz1 + 1.0
    hlen1 = np.sqrt(hx1**2 + hy1**2 + hz1**2)
    hx1, hy1, hz1 = hx1/hlen1, hy1/hlen1, hz1/hlen1
    dot_h1 = np.maximum(0.0, nx*hx1 + ny*hy1 + nz*hz1)
    spec_sharp = dot_h1 ** 24.0
    spec_soft = dot_h1 ** 6.0

    # Teinte Chrome Argenté Liquide Sorayama
    # Base argent claire très pure #e4ecf5 à #fbfdff
    chrome_r = 195.0 + 35.0 * dot1 + 15.0 * dot2 + 95.0 * spec_sharp + 30.0 * spec_soft
    chrome_g = 208.0 + 32.0 * dot1 + 18.0 * dot2 + 95.0 * spec_sharp + 32.0 * spec_soft
    chrome_b = 226.0 + 26.0 * dot1 + 22.0 * dot2 + 95.0 * spec_sharp + 35.0 * spec_soft

    chrome_r = np.clip(chrome_r, 0, 255)
    chrome_g = np.clip(chrome_g, 0, 255)
    chrome_b = np.clip(chrome_b, 0, 255)

    # 6. Assemblage final
    out_arr = dark_suit.copy()
    
    # Injection du chrome avec anti-aliasing sur les bords
    for c in range(3):
        color_c = [chrome_r, chrome_g, chrome_b][c]
        out_arr[:, :, c] = out_arr[:, :, c] * (1.0 - smooth_mask) + color_c * smooth_mask

    # 7. Rainures de découpe noires (Panel lines) mécatroniques
    # Dilatation du bord des plaques pour créer des rainures d'occlusion ambiante
    edge_dil = np.array(mask_img.filter(ImageFilter.MaxFilter(size=3)), dtype=np.uint8) > 0
    groove_mask = (edge_dil & (~mask_chrome) & is_uv_mesh & (~is_protected)) | panel_lines
    out_arr[groove_mask, 0] = np.minimum(out_arr[groove_mask, 0], 12.0)
    out_arr[groove_mask, 1] = np.minimum(out_arr[groove_mask, 1], 16.0)
    out_arr[groove_mask, 2] = np.minimum(out_arr[groove_mask, 2], 24.0)

    # 8. Liserés néon cyan luminescents fins Sorayama (#00f5d4)
    neon_final = neon_lines & mask_chrome & (~is_protected)
    out_arr[neon_final, 0] = 0.0
    out_arr[neon_final, 1] = 245.0
    out_arr[neon_final, 2] = 212.0

    # 9. Préservation des ongles et mains
    out_arr[is_protected] = cur_arr[is_protected]

    # Transparence hors UV
    out_arr[~is_uv_mesh, 3] = 0.0

    final_img = Image.fromarray(out_arr.astype(np.uint8), mode='RGBA')
    final_img.save('packages/compagnon-desktop/overlay/vrm/body_skin_android.png')
    final_img.save('packages/cortex/compagnon_ui/public/vrm/body_skin_android.png')
    print("Texture Sorayama Chrome 360° générée avec succès !")

if __name__ == '__main__':
    generate_sorayama_360()
