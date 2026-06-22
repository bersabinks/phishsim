# Développer avec Claude Code

Ce guide explique comment utiliser **Claude Code** pour faire évoluer ce projet
en local : étendre le MVP, corriger, ajouter des tests, etc. Claude Code est un
outil en ligne de commande qui lit ton dépôt, propose des modifications et exécute
des commandes (tests, lint) sous ton contrôle.

---

## 1. Installation

L'installation par npm est désormais **dépréciée**. Utilise l'une des méthodes
recommandées ci-dessous (Claude Code fonctionne sur macOS, Linux et Windows).

```bash
# macOS / Linux (recommandé)
curl -fsSL https://claude.ai/install.sh | bash

# macOS / Linux via Homebrew
brew install --cask claude-code

# Windows (PowerShell, recommandé)
irm https://claude.ai/install.ps1 | iex

# Windows via WinGet
winget install Anthropic.ClaudeCode
```

Vérifie l'installation :

```bash
claude --version
```

Puis, à la racine du projet :

```bash
cd phishsim
claude
```

Au premier lancement, une procédure d'authentification dans le navigateur te
connecte à ton compte Anthropic (abonnement Pro/Max ou crédits API).

> Les commandes ci-dessus peuvent évoluer ; en cas de doute, vérifie la
> documentation officielle (code.claude.com/docs) plutôt qu'une version figée.

---

## 2. Principe d'usage

Claude Code travaille **dans le dossier courant**. Il faut donc le lancer à la
racine du dépôt pour qu'il voie `app/`, `tests/`, etc. Tu lui décris un objectif,
il propose un plan et des modifications de fichiers, exécute les tests, et te
montre le résultat. Tu valides ou tu ajustes.

Bonnes pratiques :

- **Committe avant** de lancer une grosse tâche (`git add -A && git commit`),
  pour pouvoir revenir en arrière facilement.
- Demande-lui de **lancer les tests** après chaque changement.
- Demande une **traçabilité IA** : objectif visé + ce qui a été corrigé
  manuellement (utile pour la section 6 de `docs/SCRUM.md`).

---

## 3. Fichier de contexte projet

Crée un fichier `CLAUDE.md` à la racine pour que Claude Code connaisse les règles
du projet. Il est lu automatiquement à chaque session.

```markdown
# Contexte projet — phishsim

## Règles non négociables
- Aucun envoi réel de courriel (jamais).
- Aucune collecte d'identifiant ni de mot de passe.
- Jetons non sensibles ; résultats agrégés sans classement nominatif.
- Refuser toute donnée réelle (e-mail) à l'import.

## Stack
- Python 3.12, FastAPI, SQLite, JS sans framework.
- Tests : pytest. Lint : ruff.

## Avant de terminer une tâche
- `ruff check app tests` doit passer.
- `pytest -q` doit passer.
- Mettre à jour la doc concernée dans `docs/`.
```

---

## 4. Exemples de prompts pour les extensions

Les extensions du cahier des charges sont **à faire après acceptation du MVP**.
Voici des prompts prêts à donner à Claude Code.

### Extension — Expiration automatique des jetons
```
Ajoute une tâche de fond qui marque les jetons expirés comme inactifs et
empêche tout événement sur un jeton expiré. La durée vient de
PHISHSIM_TOKEN_TTL_HOURS. Ajoute des tests couvrant un jeton expiré et un
jeton valide. Lance ruff et pytest avant de finir.
```

### Extension — Export PDF synthétique
```
Ajoute un endpoint GET /api/campaigns/{id}/export qui génère un PDF des
indicateurs agrégés (sans aucune donnée nominative). Utilise une bibliothèque
légère. Ajoute un test vérifiant que le PDF est produit et qu'aucun jeton n'y
figure. Mets à jour le README.
```

### Extension — Comparaison de campagnes
```
Ajoute une page et un endpoint comparant les taux agrégés de deux campagnes
côte à côte. Aucune donnée individuelle. Ajoute des tests d'agrégation
comparée. Respecte le style front existant (pas de framework).
```

### Extension — Bibliothèque de conseils
```
Ajoute une page /conseils listant des bonnes pratiques anti-phishing, et un
lien depuis le tableau de bord. Contenu statique, pas de base de données.
```

### Tâche — Augmenter la couverture de tests
```
Ajoute une étape de couverture (coverage) à la CI et au pytest local, avec une
cible de 80% sur app/services.py. N'altère pas le comportement existant.
```

---

## 5. Workflow recommandé pour le sprint

1. `git commit` de l'état stable actuel.
2. Lancer `claude` à la racine.
3. Donner un prompt d'extension (section 4).
4. Laisser Claude Code modifier le code et lancer `pytest`.
5. Relire la diff, ajuster si besoin, puis committer.
6. Reporter la trace IA dans `docs/SCRUM.md` (objectif + correction humaine).
7. Vérifier que la CI passe sur le dépôt distant.

---

## 6. Garde-fous à rappeler à Claude Code

Si une suggestion va à l'encontre des règles (envoi d'e-mail réel, collecte
d'identifiant, classement nominatif), **refuse-la** : ces points sont hors
périmètre et protègent le Sprint Goal. Tu peux le formuler ainsi :

```
Rappel : ne propose jamais d'envoi de courriel réel, de collecte
d'identifiant, ni d'affichage nominatif. Ces éléments sont interdits par
conception.
```
