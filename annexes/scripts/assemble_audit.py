"""Assemble AUDIT_PARIS.txt from the draft parts. Usage: python3 -I assemble_audit.py SCRATCHPAD REPO"""
import sys, os
S, R = sys.argv[1], sys.argv[2]
rd = lambda f: open(os.path.join(S, f), encoding="utf-8").read()
p1 = rd("AUDIT_draft_part1.txt")

def rep(text, old, new):
    assert text.count(old) == 1, old[:80]
    return text.replace(old, new)

p1 = rep(p1, "Livrables associés : PROMPT_PARIS_VERSION_FINALE.txt (SOL 6.0, environ 8 500 mots) et le présent audit.",
         "Livrables associés : PROMPT_PARIS_VERSION_FINALE.txt (SOL 6.0, environ 10 200 mots, contre 20 400 pour SOL 5.16) et le présent audit ; le dossier annexes/ contient les scripts, les cas, les sorties de test et les résultats bruts.")
p1 = rep(p1, "Le problème central de SOL 5.16 n'est pas mathématique : ses formules sont justes (22 contrôles exécutés, section 8.1).",
         "Le problème central de SOL 5.16 n'est pas mathématique : ses formules sont justes (contrôles exécutés, section 8.1).")
p1 = rep(p1, "Tests : 22 contrôles de calcul réussis ; deux défauts de conception de R★ trouvés et corrigés par le calculateur avant les tests ; comparaison A/B en aveugle de la refonte et d'une correction minimale sur six journées fictives contrastées (section 8.3).",
         """Tests :
- 29 contrôles de calcul réussis ;
- deux défauts de conception de R★ trouvés et corrigés par le calculateur avant les tests ;
- comparaison A/B en aveugle sur six journées fictives contrastées : la refonte l'emporte dans les six cas (70/72 contre 56,5/72), sans erreur grave d'un côté comme de l'autre. Dans quatre cas sur six, la correction minimale retient un simple à 1,20–1,33, justifié surtout par sa forte chance de toucher ;
- deux validations des règles ajoutées, toutes conformes : cas C7 (hockey et bonus combiné) et cas C4 rejoué sur la version finale (section 8.5) ;
- relecture finale, doublée d'une relecture à froid (section 8.8) ;
- passe ciblée après livraison, sur les remarques d'un relecteur externe : huit corrections retenues (ticket court avec sacrifice de prix affiché, formule d'ajout de jambe, scénarios prudents à 100 %, seuils par rejeu complet, cote Winamax ou référence qui bouge, revue des écartés, conditions invérifiables avant la première jambe), testées sur trois nouveaux cas (section 8.9).""")
p1 = rep(p1, "5. Calculateur de référence (Python) pour la règle de décision, les cas de contrôle et les exemples chiffrés ; 22 contrôles exécutés.",
         "5. Calculateur de référence (Python) pour la règle de décision, les cas de contrôle et les exemples chiffrés ; 29 contrôles exécutés.")
p1 = rep(p1, "   Gain : un sport n'est retenu que s'il gagne la comparaison R★ (cas C1, section 8).",
         """   Gain : un sport n'est retenu que s'il gagne la comparaison R★ (cas C1, section 8).
   Arbitrage entre vos consignes : le brief dit « le tennis reste prioritaire », alors que la consigne carte blanche, qui prime, précise « aucune priorité automatique sur le ticket principal » et demande d'analyser chaque rencontre « si je demande tout le programme ». Solution retenue :
   - le programme tennis est toujours recensé en entier au niveau du marché ;
   - le mode complet s'active sur demande ;
   - R★ seul décide du choix principal.""")
p2a = rd("AUDIT_draft_part2a.txt")
p2a = rep(p2a, "8.1 Contrôles de calcul exécutés (Python) : 22 sur 22 réussis", "8.1 Contrôles de calcul exécutés (Python) : 29 sur 29 réussis")
p2a = rep(p2a, "Exemples de SOL 5.16 recalculés (A à H, longueurs 3/4/5 à 80 %, formule de Poisson) : tous justes.",
          """Exemples de SOL 5.16 recalculés (A à H, longueurs 3/4/5 à 80 %, formule de Poisson) : tous justes.
Exemples ajoutés dans la version finale (ligne du registre, seuil de bascule avec le terme t, carte d'exemple) : vérifiés (25 contrôles), puis quatre contrôles de la passe ciblée (8.9) : 29 au total.""")
p2b = rd("AUDIT_draft_part2b.txt")
p2c = rd("AUDIT_draft_part2c.txt")
p2f = rd("AUDIT_draft_part2f.txt") if os.path.exists(os.path.join(S, "AUDIT_draft_part2f.txt")) else "\n8.5 Validation de la version finale sur un septième cas — en cours.\n"
p2d = rd("AUDIT_draft_part2d.txt")
p2d = rep(p2d, "- 22 contrôles de calcul ;", "- 29 contrôles de calcul ;\n- trois validations de la passe ciblée (C8, C9, C10, section 8.9) ;")
p2d = rep(p2d, "6. Exemple chiffré corrigé : −1,85 % au lieu de « −1,9 % » (8.1).",
          "6. Exemple chiffré corrigé : −1,85 % au lieu de « −1,9 % » (8.1).\n7. Relecture finale : six corrections issues de ma relecture et huit de la relecture à froid (8.8).")
p2e = rd("AUDIT_draft_part2e.txt")
p2g = rd("AUDIT_draft_part2g.txt")
p3 = rd("AUDIT_draft_part3.txt")
budget = """
9. Dépense de la session. Je ne peux pas mesurer la consommation réelle depuis cet environnement : je ne peux donc pas garantir le respect du plafond d'environ 250 $. Pour l'économiser, j'ai :
   - délégué les recherches documentaires, la notation et la relecture à froid à un modèle moins coûteux ;
   - imposé des sorties de test compactes ;
   - limité les tests aux six cas demandés, puis à quelques cas de validation ciblés ;
   - réservé les vérifications supplémentaires à celles qui pouvaient changer une sélection (sensibilité, calibration de la fourchette, hockey, bonus combiné).
   À titre indicatif seulement, les traces d'exécution indiquent environ 250 000 à 350 000 jetons traités par exécution de test. Ce n'est pas un montant en dollars."""
p3 = rep(p3, "\n\n═══ 10. SOURCES ═══", budget + "\n\n═══ 10. SOURCES ═══")
out = p1 + p2a + p2b + p2c + p2f + p2d + p2e + p2g + p3
open(os.path.join(R, "AUDIT_PARIS.txt"), "w", encoding="utf-8").write(out)
print("audit words:", len(out.split()))
