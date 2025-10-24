## 2025/10/24 


### Présentation générale 

- Le bus d'extraction comment ça marche et comment l'utiliser ? 
L'avantage est qu'on peut monter ou descendre à n'importe quel arrêt. Chaque composant est relativement indépendant des autres : 

Les 3 composants sont : 
    - Un service Karton 
    - La librairie ConfigExtractor du CERT Canada
    - L'extracteur lui-même 


Le service Karton 

- Le service Karton est chargé d'instancer un ConfigExtractor 
- Boucle sur les extracteurs fournit en configuration 
- Appelle la fonction run_parsers du ConfigExtracteur en lui fournissant le sample à analyser 
- Si une configuration est extraite, on arrête la boucle sur les extracteurs 

Remarque : ce desgin ne parait pas totalement tirer parti des capacitié multi thread de la librarie puisqu'on charge un seul extracteur à la fois => cela dépend de la structure de fichier et du fichier de configuration. 


La librairie ConfigExtractor est un framework qui permet essentiellement : 
    - de normaliser les données, pour nous format MAco mais a
    - de filtrer les extracteurs par règle YARA 
    - d'appeler dynamiquement l'extracteur et son contexte venv 


L'extracteur qui est la partie que nous implémentons : 
    - extract.py est l'extracteur en lui-même, avec tout le code nécessaire et spécfique à l'extraction sur une famille de malware 
        - il peut être exécuté en ligne de commande 
        - ou chargé comme un module python et lancer via la fonction extract 
    - Maco.ExtractorModel qui structure les données extraites au format Maco. Il est le fichier nécessaire qui fait la jonction entre l'extracteur et la librairie COnfigExtractor, via la fonction run() qui appelée dynamqiquement par la librairie 


 
### Modèle de données : 

    - dans l'exemple ANSSI / Amadey l'extracteur renvoie une classe MAadey config. Nous étions habitués à du json mais ici ça n'a pas grande importance puisque ces le MACO.ExtractorModel qui va formater les données. 

    - dans un 2nd temps nous avons un format MACO qui est renvoyé à la librairie 

    - la librairie va transformer ce format en dictionnaire, ajoutant au passage des métas informations sur l'author, la description etc... qu'elle a parsé dans le fichier MACO.ExtractorModel 

    - finalement elle encapsule une dernière fois le dictionnaire dans une liste associée au framework utilisé 


### Le code, ce que nous avons fait : 

- extracteur.py 
    - argparse + Ajout des arguments (log, log_file, json_export, verbose)
    - modification du logger pour l'associé au module (vs root logger) 
    - modification de la fonction de configuration du logger : StreamHandler + FileHandler + verbosity
    - modifications des signatures des fonction extract et extract_on_file_path : 2 arguments nommés: content et verbosity + ajout de **kwargs pour les besoins spécifiques. 
    - modification de la fonction extract => ajout de l'export json vers un fichier => si on le fait sur un extract on le fait à un seul endroit 
    - abandon des codes de retour ?

- Class Example : 
    - ajout d'une fonction run_for_tracker qui : 
        - est un wrapper de la fonction run 
        - permet d'utiliser les arguments de l'extracteur 
        - utilise run()->extract et pas un filepath pour que le code prenne le même chemin que celui de la library ConfigExtractor. => tests , fiabilité 


2 modèles de launcher : 
    - simple_launcher : utilise uniquement l'extracteur est reçoit une configuration Maco 
    - confextractor_launcher : utilise la librairie ConfExtractor



    
