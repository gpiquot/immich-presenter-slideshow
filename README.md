# Immich Presenter et Slideshow

Sources de référence utilisées avec Immich 2.7.5, conservées avant
la préparation de l'upgrade vers Immich 3.1.2.

La compatibilité avec Immich 3.1.2 n'est pas encore validée.
Le test de restauration est reporté.

## Organisation

- presenter/ : serveur Python, interface et générateur de liens.
- slideshow/ : script HTML de diaporama distinct, conservé comme référence.
- deployment/ : copie de la définition du service systemd.

Installations actuelles :
- /opt/immich_presenter
- /opt/immich_slideshow

Le dépôt de préparation ne remplace pas ces installations.

## Environnement constaté

- Python système : 3.12.3, /usr/bin/python3
- Flask : 3.0.2
- requests : 2.31.0
- python-dotenv : 1.0.1

Modules présents dans /usr/lib/python3/dist-packages.
Les versions exactes des paquets Ubuntu restent à relever.

Le service immich-presenter.service s'exécute sous ubuntu:ubuntu.
Il lance directement server.py, sans environnement virtuel.

## Configuration et secrets

server.py charge /opt/immich_presenter/.env.

.env.example décrit les variables à renseigner ; ses valeurs doivent
être adaptées à l'installation. Le véritable .env est exclu de Git.

IMMICH_API_KEY sert aux appels serveur vers Immich.
PRESENTER_TOKEN autorise l'édition depuis les liens présentateur.
DEFAULT_SHARE_KEY est facultatif si la clé est fournie dans l'URL.
ALBUM_NAME active un mode album de secours à réserver à un usage local.

Le token de make-presenter-url.sh a été remplacé par une valeur factice
dans cette sauvegarde. Il faut le configurer pour utiliser ce script.
Son externalisation sera réalisée dans un changement ultérieur.

Les secrets existants doivent être conservés séparément, dans une
sauvegarde protégée. Ce dépôt seul ne suffit pas à restaurer le service.

## Fonctions de Presenter

Presenter intègre la grille, le diaporama et l'édition des descriptions.

- Clic sur une vignette : démarrer le diaporama.
- T : basculer grille/diaporama.
- Flèches : photo précédente ou suivante.
- Espace : pause/reprise ; la reprise passe à la photo suivante.
- D : maintenir ou masquer la description.
- E : éditer, avec un lien présentateur autorisé.
- Ctrl+E : enregistrer.
- Échap : annuler l'édition ou revenir à la grille.

Durée d'une photo :
5000 + min(8000, longueur de la description nettoyée × 35) millisecondes.

La description apparaît après 700 ms. Son affichage temporaire dure :
min(8000, 1500 + longueur de la description nettoyée × 35) millisecondes.

## Points connus conservés dans la référence

- Accolade fermante manquante après .thumb.active dans style.css.
- Temporisations lancées avant la fin du chargement de l'image.
- Cache des sources sans expiration.
- Description XMP prioritaire sur le champ description lu dans l'API.
- La sauvegarde d'une description passe par l'API Immich ; le serveur
  Presenter ne réécrit pas lui-même les XMP. Persistance à vérifier.
- Le script slideshow.html utilise une durée fixe de six secondes et
  attend des éléments HTML absents du fichier reçu. Son contexte
  d'utilisation reste à documenter.

Ces points ne sont pas corrigés dans la référence avant upgrade.

## Principes de restauration — procédure non testée

1. Récupérer le tag immich-2.7.5-baseline.
2. Préparer Python et les dépendances correspondant à l'environnement.
3. Copier le contenu de presenter/ vers /opt/immich_presenter.
4. Restaurer le .env protégé séparément et vérifier les chemins XMP.
5. Adapter et installer le service fourni dans deployment/.
6. Rétablir la configuration du proxy HTTP existant, à documenter.
7. Vérifier lecture et édition sur un album de test avant remise en service.

Ne pas appliquer ces étapes à l'installation active sans sauvegarde.
Le rôle et le déploiement du slideshow distinct restent à confirmer.
