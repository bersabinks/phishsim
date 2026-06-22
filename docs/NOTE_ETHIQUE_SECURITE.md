# Note éthique et sécurité

Exigée par les consignes du Product Owner. Ce document explique pourquoi le
produit reste **défensif et pédagogique**, et comment les risques sont maîtrisés.

## 1. Cadre et intention

L'outil sert à **sensibiliser** des collaborateurs au phishing au moyen de
**simulations contrôlées**. Il ne reproduit aucun mécanisme offensif réel : pas
d'envoi de courriel, pas de capture d'identifiants, pas d'usurpation.

## 2. Risques identifiés et mesures

| Risque | Mesure dans le produit |
|---|---|
| Dérive vers un outil offensif | Aucune fonction d'envoi de courriel ; garde-fou bloquant au démarrage ; page de simulation purement informative. |
| Collecte de données personnelles | Refus des adresses e-mail à l'import ; alias fictifs uniquement ; aucun champ de mot de passe. |
| Réidentification des participants | Résultats strictement agrégés ; aucun classement nominatif ; jetons non sensibles. |
| Fuite d'information par les logs | Messages d'erreur génériques côté client ; pas de journalisation de jeton complet ni de donnée personnelle. |
| Jetons devinables | Génération par `secrets.token_urlsafe` (aléa cryptographique) ; expiration configurable. |
| Injection / falsification d'entrée | Validation systématique des entrées ; requêtes SQL paramétrées ; échappement HTML à l'affichage. |
| Chaîne de livraison compromise | CI avec analyse de dépendances (`pip-audit`) et recherche de secrets (`gitleaks`). |

## 3. Conformité à la vie privée

- Aucune donnée personnelle réelle n'est traitée : la base ne contient que des
  alias fictifs et des compteurs.
- Principe de minimisation : on ne stocke que ce qui est nécessaire à
  l'agrégation pédagogique.
- Les jetons peuvent expirer automatiquement (configuration `TOKEN_TTL_HOURS`).

## 4. Limites assumées

- Le produit ne prétend pas mesurer la « culpabilité » individuelle : l'objectif
  est l'amélioration collective, pas la sanction.
- En contexte réel d'entreprise, une campagne de sensibilisation doit être
  encadrée par une information préalable des personnes et le respect du cadre
  légal applicable (ex. RGPD, accord des représentants du personnel).

## 5. Décision produit

Conformément au rôle du Product Owner, tout élément menaçant ces principes (envoi
réel, collecte d'identifiants, classement nominatif) est **hors périmètre** et
peut être retiré à tout moment pour protéger le Sprint Goal.
