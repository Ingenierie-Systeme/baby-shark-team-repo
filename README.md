# baby-shark

<p align="center">
  <img src="docs/img/robot_complet.jpg" alt="Le robot Baby Shark assemblé" width="700">
</p>

Robot sous-marin biomimétique (requin) propulsé par une nageoire actionnée par servomoteurs.
Ce dépôt regroupe le code embarqué ROS 2 et les fichiers de conception du robot.

## Organisation du dépôt

```
baby-shark-team-repo/
├── ros2_ws/                 ← code embarqué (seul dossier nécessaire sur le robot)
│   └── src/
│       └── navigator/       ← package ROS 2 : capteurs, radiocommande, fusion, servos
├── mecanique/               ← CAO, pièces, plans (jamais téléchargés sur le robot)
├── docs/img/                ← images du README et du carnet de bord
└── README.md
```

> Les fichiers de conception (`.ipt`, `.obj`, `.stl`…) vont dans `mecanique/` et **pas à la racine** :
> le robot récupère toujours les fichiers de la racine, seuls les sous-dossiers sont filtrés.

## Matériel

| Élément | Rôle | Interface |
|---|---|---|
| Raspberry Pi 4 + Blue Robotics Navigator v2 | Calculateur, IMU, magnétomètre, sorties PWM | — |
| Récepteur radio SBUS | Télécommande manuelle | UART `/dev/ttyS0` |
| Capteur MS5837-30BA | Pression → profondeur (eau salée) | I2C bus 6 |
| 2 servomoteurs | Nageoire | PWM 50 Hz, canaux 0 et 1 |

Logiciel : Ubuntu 24.04, ROS 2 Jazzy.

## Architecture ROS 2

<img width="886" height="530" alt="image" src="https://github.com/user-attachments/assets/9be415e7-d70d-4ec7-8ad1-15d062d86fdd" />


En pointillés : le node `control`, pas encore écrit.

### Nodes

| Node | Fichier | Rôle |
|---|---|---|
| `navigator` | `node_navigator.py` | Lit l'IMU et le magnétomètre à 100 Hz, applique les commandes servos en PWM |
| `rc` | `node_rc.py` | Décode les trames SBUS (8 voies normalisées entre -1 et 1) |
| `baro` | `node_baro.py` | Lit la profondeur à 10 Hz |
| `fusion` | `node_fusion.py` | Estime l'attitude (AHRS `imufusion`, convention NED) |
| `control` | *à écrire* | Commande des servos à partir de la RC et de l'état |
| `navigation` | *à écrire* | — |

### Topics

| Topic | Type | Publié par | Souscrit par |
|---|---|---|---|
| `/input/rc` | `std_msgs/Float32MultiArray` | `rc` | (`control`) |
| `/input/imu` | `sensor_msgs/Imu` | `navigator` | `fusion` |
| `/input/mag` | `sensor_msgs/MagneticField` | `navigator` | `fusion` |
| `/input/depth` | `std_msgs/Float32` | `baro` | (`control`) |
| `/state/attitude` | `sensor_msgs/Imu` (orientation) | `fusion` | (`control`) |
| `/output/servos` | `std_msgs/Float32MultiArray` (2 valeurs, -1 à 1) | (`control`) | `navigator` |

Commande servo : -1 → 1000 µs, 0 → 1500 µs, +1 → 2000 µs.
`data[0]` sort sur le canal PWM 1, `data[1]` sur le canal PWM 0.

## Installation sur le robot

### 1. Dépendances

```bash
sudo apt install git python3-numpy python3-serial python3-smbus2
pip install bluerobotics-navigator imufusion --break-system-packages
```

ROS 2 Jazzy doit être installé (`ros-jazzy-ros-base`).

### 2. Récupérer uniquement le code embarqué

Une clé SSH du robot doit être ajoutée au compte GitHub (Settings → SSH and GPG keys).

```bash
cd ~
git clone --filter=blob:none --sparse git@github.com:Ingenierie-Systeme/baby-shark-team-repo.git
cd baby-shark-team-repo
git sparse-checkout set ros2_ws
```

### 3. Compiler

```bash
cd ~/baby-shark-team-repo/ros2_ws
colcon build --symlink-install
echo "source ~/baby-shark-team-repo/ros2_ws/install/setup.bash" >> ~/.bashrc
source ~/.bashrc
```

## Utilisation

Tout lancer :

```bash
ros2 launch navigator all.launch.py
```

Lancer un seul node :

```bash
ros2 run navigator baro
```

Vérifier ce qui tourne :

```bash
ros2 topic list
ros2 topic echo /input/depth
rqt_graph
```

## Travailler avec Git

Sur le robot comme sur un PC :

```bash
cd ~/baby-shark-team-repo
git pull                       # récupérer le travail de l'équipe
# ... modifications ...
git add ros2_ws
git commit -m "Description du changement"
git push
```

Ne jamais committer `build/`, `install/` ni `log/` (déjà dans `ros2_ws/.gitignore`).

## Équipe

tbelier · guilhemmerlet19-ai · anatolelb · yoann-mtrz

---

## 📓 Carnet de bord

Avancement du projet, point d'étape par point d'étape (d'après les présentations de suivi).

### 26 octobre — Lancement

<img src="docs/img/2610_concept.png" alt="Concept du robot" width="220" align="right">

Présentation du projet : un **robot ondulatoire d'exploration et d'observation**, inspiré d'un AUV existant (environ 7 300 € pour le premier modèle, essentiellement en main d'œuvre).
L'objectif est d'en faire une version à notre échelle avec une propulsion par nageoire.

<br clear="right">

### 28 octobre — De la CAO aux premières pièces

**Conception 3D.** On part d'un modèle en accès public et on dessine les deux pièces qui manquent : la jonction entre le moteur de propulsion et la pale, et le bouchon qui ferme le tube de façon étanche.

<table>
  <tr>
    <td><img src="docs/img/2810_modele_public.jpg" alt="Modèle public" width="380"></td>
    <td><img src="docs/img/2810_pieces_concues.jpg" alt="Pièces conçues" width="300"></td>
  </tr>
  <tr>
    <td align="center"><sub>Modèle de départ</sub></td>
    <td align="center"><sub>Jonction moteur/pale et bouchon d'étanchéité</sub></td>
  </tr>
</table>

**Impression et récupération des pièces.** La jonction est imprimée en filament, le bouchon en résine. On récupère aussi le tube transparent et le couvercle étanche.

<table>
  <tr>
    <td><img src="docs/img/2810_assemblage_impression.jpg" alt="Assemblage des pièces imprimées" width="260"></td>
    <td><img src="docs/img/2810_tube.jpg" alt="Tube" width="260"></td>
    <td><img src="docs/img/2810_couvercle.jpg" alt="Couvercle étanche" width="260"></td>
  </tr>
  <tr>
    <td align="center"><sub>Pièces imprimées assemblées</sub></td>
    <td align="center"><sub>Tube</sub></td>
    <td align="center"><sub>Couvercle étanche</sub></td>
  </tr>
</table>

**Masse interne mobile.** Premier essai du rail qui déplace une masse dans le tube pour régler l'assiette ; une pièce complémentaire est en cours d'impression.

<img src="docs/img/2810_masse_interne.jpg" alt="Déplacement de la masse interne" width="380">

**Simulation et électronique.** Le robot est importé dans Unity. Côté électronique, le schéma de câblage est posé (batterie, module de puissance, BEC 5 V, Raspberry + Navigator, deux servos, capteur de pression, caméra) et les cartes sont reliées sur table. La Raspberry est flashée sous Ubuntu, accessible en SSH, avec le dépôt en sparse checkout.

<table>
  <tr>
    <td><img src="docs/img/2810_unity.jpg" alt="Première scène Unity" width="260"></td>
    <td><img src="docs/img/2810_schema_electrique.png" alt="Schéma électrique" width="260"></td>
    <td><img src="docs/img/2810_electronique.jpg" alt="Électronique sur table" width="260"></td>
  </tr>
  <tr>
    <td align="center"><sub>Première scène Unity</sub></td>
    <td align="center"><sub>Schéma électrique</sub></td>
    <td align="center"><sub>Électronique câblée sur table</sub></td>
  </tr>
</table>

### 2 novembre — Premier robot complet

Toutes les pièces sont assemblées : le robot existe pour la première fois en entier (photo en haut de page). L'électronique est montée à bord, et les nodes moteur et baromètre ont été testés sur le robot.

**Déplacement de masse par pignon-crémaillère.** Le rail du 28 octobre devient un système pignon-crémaillère, entraîné par un servo.

<img src="docs/img/0211_cremaillere_cao.jpg" alt="CAO du système pignon-crémaillère" width="420">

**Nageoires.** Ajout d'une nageoire dorsale, de nageoires pectorales et de la nageoire caudale.

<table>
  <tr>
    <td><img src="docs/img/0211_nageoires_dorsale.jpg" alt="Nageoires dorsale et pectorales" width="230"></td>
    <td><img src="docs/img/0211_nageoire_caudale.jpg" alt="Nageoire caudale" width="300"></td>
  </tr>
  <tr>
    <td align="center"><sub>Dorsale et pectorales</sub></td>
    <td align="center"><sub>Caudale</sub></td>
  </tr>
</table>

**Unity.** La scène reprend maintenant l'intérieur réel du tube : rail, masse mobile et électronique.

<img src="docs/img/0211_unity.jpg" alt="Modèle Unity détaillé" width="420">

### 4 novembre — Premier passage au bassin

**Test d'étanchéité.** Premier passage dans l'eau. L'eau s'infiltre entre le premier et le deuxième joint du bouchon : l'étanchéité est à reprendre.

<table>
  <tr>
    <td><img src="docs/img/0411_bassin.jpg" alt="Robot dans le bassin" width="220"></td>
    <td><img src="docs/img/0411_etancheite.jpg" alt="Infiltration entre les joints" width="230"></td>
  </tr>
  <tr>
    <td align="center"><sub>Mise à l'eau</sub></td>
    <td align="center"><sub>Eau entre les deux joints</sub></td>
  </tr>
</table>

**Mécanique.** La crémaillère est maintenant tenue des deux côtés, et deux nageoires latérales ont été ajoutées. Dans Unity, la vraie mécanique et un environnement complet sont intégrés.

<img src="docs/img/0411_cremaillere.jpg" alt="Crémaillère maintenue des deux côtés" width="420">

**ROS 2.** Les nodes `control` et `camera` sont terminés. L'architecture se découpe en trois blocs : capteurs, intelligence et actionneurs. Les messages `/input/depth` et `raw_img` sont aussi publiés depuis la simulation Unity.

<img src="docs/img/0411_schema_ros2.png" alt="Schéma des nodes ROS 2 mis à jour" width="500">

### Prochaines étapes

- [ ] Reprendre l'étanchéité du bouchon et refaire un test au bassin (flottabilité comprise)
- [ ] Ajouter la pièce de soutien de la crémaillère
- [ ] Brancher la caméra et ROS 2 sur Unity
- [ ] Finir `node_navigation.py` et tester les nodes en réel et en simulation
