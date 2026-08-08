# Lot 07 — pages publiques de confiance

Ce lot ajoute trois éléments gratuits nécessaires à la préparation du lancement :

- une page publique `/contact` qui oriente vers les parcours internes adaptés ;
- une déclaration `/accessibility` honnête, sans fausse certification ;
- des mentions légales accessibles sur `/legal/notice` ;
- la mise à jour du routeur, du pied de page et du sitemap ;
- l’extension des tests Playwright publics.

## Installation

Depuis la racine du projet Mbolo :

```bash
unzip -o /mnt/c/Users/User/Downloads/mbolo-public-trust-batch-07.zip
cd frontend
npm run check
npm run test:e2e:public
cd ..
git diff --check
git status -sb
```

Les mentions légales contiennent volontairement des champs « à compléter avant
lancement ». Ils devront recevoir l’identité juridique et l’adresse réelles de
l’éditeur lorsque la structure définitive de Mbolo sera choisie.
