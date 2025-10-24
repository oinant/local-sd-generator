# Braindump

## Ideas to implement

- Tag the model used for generation in file metadata (call the api? use an headless browser?)
- use variation names & variant keys in file name : {Session_name}_index_{variationName_variantKey}
- ~~CLI : add scheduler in parameters~~ DONE
- ~~CLI : refacto l'UX de la CLI avec Typer~~ DONE
- le renew token (qui doit etre effectif quasi immédiatement dans la web ui, on doit la restart?)
- le split des commandes
- l'affichage du sdgen start encore un peu messy (en prod, on affiche l'url du front en dev-mode)
- ~~un moyen de lancer un "build" (linting + tu + coverage + type check + compil du front...)~~ DONE
- CLI : option de selecteur interactif pour les place holders
- CLI : option pour "etendre" une session : on a lancer 5-10 images pour tester un prompt et des variation, ca nous plait, alors on peut repartir sur cette session directement sans avoir a créer un nouveau dossier : possible car les métadatas contiennent a la fois les variation et les combinaisons deja utilisées
- WEB UI : flag les générations ratées (image par image). Peut permettre de comprendre ce qui ne fonctionne pas dans le prompt et pourquoi (avec analyse des prompts) (base sqlite?)
- WEB UI : systeme de tri/filtrage des images d'une session, sur base des options de variations dans le manifest 
- CORE : passer la version actuelle du manifest à 4.0
