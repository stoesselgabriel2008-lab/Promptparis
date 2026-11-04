ANNEXES DE L'AUDIT — de quoi vérifier ou refaire chaque résultat cité dans AUDIT_PARIS.txt

Ce dossier ne contient ni le fichier SOL 5.16 d'origine (il reste chez son auteur) ni les données brutes. Les scripts permettent de retélécharger ces données.

scripts/
- calc.py : calculateur de référence (retrait de marge power et multiplicatif, règle de décision R★, énumération des tickets, seuil de bascule).
- tests_calc.py : contrôles automatiques (31), lancés par « python3 -I tests_calc.py scripts/ ».
- prompt_checks.py : contrôles statiques du prompt avant chaque sauvegarde (renvois, blocs obligatoires, formulations obsolètes, numérotation, longueur).
- gen_c11_c13.py : génération des cas de stress C11 à C13 et de leur vérité de calcul.
- cases_v7.py : vérité de calcul des cas C8 à C10 (passe ciblée v7 : rejeu des seuils, ticket court, paiements à plusieurs états, bonus).
- assemble_audit.py : assemblage de l'audit à partir de ses parties.
- cases_build.py : vérité de calcul des cas de contrôle C1 à C6.
- sensitivity.py : sensibilité de R★ aux conventions et calibration de la fourchette. Demande les données ci-dessous.
- fb_analysis.py : étude football. Données attendues : fichiers de football-data.co.uk (https://www.football-data.co.uk/mmz4281/SAISON/LIGUE.csv), nommés LIGUE_SAISON.csv. Ligues : E0, E1, D1, I1, SP1, F1, F2, N1, P1 ; saisons : 1516 à 2526.
- espn_collect.py et us_analysis.py : collecte (API publique d'ESPN, requêtes espacées) puis étude NBA et NHL, saisons régulières 2024-25 et 2025-26.
- blind.py : mise à l'aveugle des sorties pour la notation.

resultats/
- Sorties exactes des scripts : fb_results.txt, us_results.txt, sensitivity_results.txt, tests_calc_results.txt, cas_v7_verite_de_calcul.txt.

tests/
- cas/ : les treize cas de contrôle fictifs (C1 à C6 pour le test A/B ; C7 pour la validation de la v4 ; C8 à C10 pour la passe ciblée v7 ; C11 à C13, cas de stress des révisions 6.x : tennis complet à vingt matchs, marchés vivants, freebet et bilan de journal).
- verite_de_calcul/ : vérité de calcul et erreurs graves, fixées avant les exécutions ; consignes des évaluateurs ; correspondance X/Y ; récapitulatif des notes.
- sorties/ : les douze réponses du test A/B (suffixe _R = refonte SOL 6.0 v1 ; suffixe _M = correction minimale), plus les validations : C7_R4.txt (v4), C4_R6.txt (v6), C8_R7.txt, C9_R7.txt et C10_R7.txt (version finale v7), puis C11_R64.txt (avec son rapport TXT), C12_R64.txt et C13_R64.txt (révision 6.4).
- variantes/ : le correctif d'une page qui, placé devant SOL 5.16, formait la « correction minimale », ainsi que les versions 1 (test A/B), 4 (cas C7) et 7 (cas C8 à C10, identique à la version livrée) de la refonte telles qu'elles ont été testées.

La version livrée, PROMPT_PARIS_VERSION_FINALE.txt, intègre les corrections faites après ces tests ; la liste figure dans l'audit (sections 8.6, 8.8 et 8.9), puis, pour les révisions 6.1 et suivantes, dans JOURNAL_DES_AMELIORATIONS.txt.
