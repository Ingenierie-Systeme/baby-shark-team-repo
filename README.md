# baby-shark

Robot sous-marin biomimétique (requin) propulsé par une nageoire actionnée par servomoteurs.
Ce dépôt regroupe le code embarqué ROS 2 et les fichiers de conception du robot.

## Organisation du dépôt

```
baby-shark-team-repo/
├── ros2_ws/                 ← code embarqué (seul dossier nécessaire sur le robot)
│   └── src/
│       └── navigator/       ← package ROS 2 : capteurs, radiocommande, fusion, servos
├── mecanique/               ← CAO, pièces, plans (jamais téléchargés sur le robot)
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

```mermaid
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
