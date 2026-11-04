ANNEXES DE L'AUDIT — de quoi vérifier ou refaire chaque résultat cité dans AUDIT_PARIS.txt

Ce dossier ne contient ni le fichier SOL 5.16 d'origine (il reste chez son auteur) ni les données brutes. Les scripts permettent de retélécharger ces données.

scripts/
- calc.py : calculateur de référence (retrait de marge power et multiplicatif, règle de décision R★, énumération des tickets, seuil de bascule).
- tests_calc.py : contrôles automatiques (25), lancés par « python3 -I tests_calc.py scripts/ ».
- cases_build.py : vérité de calcul des cas de contrôle C1 à C6.
- sensitivity.py : sensibilité de R★ aux conventions et calibration de la fourchette. Demande les données ci-dessous.
- fb_analysis.py : étude football. Données attendues : fichiers de football-data.co.uk (https://www.football-data.co.uk/mmz4281/SAISON/LIGUE.csv), nommés LIGUE_SAISON.csv. Ligues : E0, E1, D1, I1, SP1, F1, F2, N1, P1 ; saisons : 1516 à 2526.
- espn_collect.py et us_analysis.py : collecte (API publique d'ESPN, requêtes espacées) puis étude NBA et NHL, saisons régulières 2024-25 et 2025-26.
- blind.py : mise à l'aveugle des sorties pour la notation.

resultats/
- Sorties exactes des scripts : fb_results.txt, us_results.txt, sensitivity_results.txt, tests_calc_results.txt.

tests/
- cas/ : les sept cas de contrôle fictifs (C1 à C6 pour le test A/B, C7 pour la validation de la version finale).
- verite_de_calcul/ : vérité de calcul et erreurs graves, fixées avant les exécutions ; consignes des évaluateurs ; correspondance X/Y ; récapitulatif des notes.
- sorties/ : les douze réponses du test A/B. Suffixe _R = refonte SOL 6.0 v1 ; suffixe _M = correction minimale.
- variantes/ : le correctif d'une page qui, placé devant SOL 5.16, formait la « correction minimale », et la version 1 de la refonte telle qu'elle a été testée.

La version livrée, PROMPT_PARIS_VERSION_FINALE.txt, intègre les corrections faites après ces tests ; la liste figure dans l'audit, sections 8.6 et 8.8.
