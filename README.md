# Boulangerie - Choisis ton Pain !!!!

Une petite application Windows en Python/Tkinter.

## Lancer l'application (dev)

1. Installez Python 3.9+ (Windows).
2. Ouvrez un terminal dans ce dossier et installez les dépendances :

```bash
pip install -r requirements.txt
```
3. Lancez :
```bash
python app.py
```

## Préparer les images

- Placez les images d'arrière-plan dans `assets/Boulangerie/` (une image sera choisie au hasard).
- Placez **une** ou plusieurs images mauvaises dans `assets/Mauvais Pain/`.
- Placez **au moins une** image correcte dans `assets/Bon pain/` (une sera choisie comme *le bon pain*).

Formats supportés : .png, .jpg, .jpeg, .webp, .bmp, .gif

## Emballer en .exe (PyInstaller)

```bash
pip install pyinstaller
pyinstaller --noconsole --onefile --add-data "assets;assets" app.py
```
Le binaire se trouvera dans `dist/app.exe`.

## Notes
- Message mauvais choix : "Ce pain n'est malheureusement plus disponible"
- Message gagnant : "Félicitations, vous avez trouvé votre pain, prenez contact avec votre pain au 0683292572 <3"
- Une animation de coeurs apparaît quand l'utilisateur choisit la bonne photo.
