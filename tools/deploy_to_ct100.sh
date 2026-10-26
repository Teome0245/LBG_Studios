#!/bin/bash
set -e

DIR="/home/lbg/projects/LBG_Studios/packages/compagnon-desktop/overlay/vrm"
FILES="body_skin_android.png face_skin_android.png hair_android.png metallic_matcap.png rim_multiply_mask.png vrm_pet.bundle.js"

echo "Test de connexion SSH vers CT100 (192.168.0.100)..."
if ssh -o BatchMode=yes -o ConnectTimeout=3 root@192.168.0.100 "docker ps --format '{{.Names}}'" 2>/dev/null | grep -q "lbg-frontend"; then
    echo "CT100 root accessible, injection dans lbg-frontend..."
    for f in $FILES; do
        scp -q "$DIR/$f" "root@192.168.0.100:/tmp/$f"
        ssh root@192.168.0.100 "docker cp /tmp/$f lbg-frontend:/usr/share/nginx/html/vrm/$f && rm /tmp/$f"
        echo " - $f injecté dans lbg-frontend"
    done
    ANIM_FILES="dance.vrma samba.vrma hiphop.vrma"
    for a in $ANIM_FILES; do
        if [ -f "$DIR/animations/$a" ]; then
            scp -q "$DIR/animations/$a" "root@192.168.0.100:/tmp/$a"
            ssh root@192.168.0.100 "docker cp /tmp/$a lbg-frontend:/usr/share/nginx/html/vrm/animations/$a && rm /tmp/$a"
            echo " - animations/$a injecté dans lbg-frontend"
        fi
    done
    echo "Déploiement CT100 réussi !"
elif ssh -o BatchMode=yes -o ConnectTimeout=3 lbg@192.168.0.100 "docker ps" 2>/dev/null; then
    echo "CT100 lbg accessible..."
else
    echo "SSH direct sans clé vers CT100 non disponible ou pas de daemon Docker direct. Vérification..."
fi
