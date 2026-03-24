# RELEVANCE_MATRIX — Clawith Fork Custom Features

**Date:** 24 mars 2026  
**Audité par:** Claw (Code Audit Lead)  
**Méthodologie:** Scoring par critère (✅/⚠️/❌)

---

## 📊 Matrice de Pertinence

### Légende

| Score | Signification |
|-------|---------------|
| ✅ | Oui / Actif / Aligné |
| ⚠️ | Partiel / Besoin refactor |
| ❌ | Non / Obsolète / Pas aligné |

---

## 1. AgentMail Integration

| Critère | Question | Score | Notes |
|---------|----------|-------|-------|
| **Utilisé?** | Est-ce que c'est activement utilisé? | ✅ | Actif en prod, API key configurée |
| **Aligné upstream?** | Est-ce que upstream a évolué dans la même direction? | ❌ | Feature custom, pas dans upstream |
| **Documenté?** | Est-ce que c'est bien documenté? | ✅ | Code bien commenté, docstring complète |
| **Testé?** | Est-ce que ça marche vraiment? | ⚠️ | Pas de tests unitaires visibles |
| **Dette technique?** | Code propre ou besoin refactor? | ✅ | Code propre, 373 lignes, structuré |

**Verdict:** ✅ **GARDER** — Feature unique, critique pour email

**Priority:** P0  
**Effort:** 0 (déjà fonctionnel)

---

## 2. Infisical MCP + Secrets

| Critère | Question | Score | Notes |
|---------|----------|-------|-------|
| **Utilisé?** | Est-ce que c'est activement utilisé? | ✅ | Actif en prod, env vars configurées |
| **Aligné upstream?** | Est-ce que upstream a évolué dans la même direction? | ⚠️ | Upstream a une approche différente |
| **Documenté?** | Est-ce que c'est bien documenté? | ✅ | Code commenté, docstrings |
| **Testé?** | Est-ce que ça marche vraiment? | ⚠️ | Pas de tests unitaires visibles |
| **Dette technique?** | Code propre ou besoin refactor? | ✅ | Code propre (147 + 617 lignes) |

**Verdict:** ✅ **GARDER** — Gestion des secrets, critique pour sécurité

**Priority:** P0  
**Effort:** 0 (déjà fonctionnel)

---

## 3. Gateway API Enhanced

| Critère | Question | Score | Notes |
|---------|----------|-------|-------|
| **Utilisé?** | Est-ce que c'est activement utilisé? | ✅ | Critique pour Clawith Repair sync |
| **Aligné upstream?** | Est-ce que upstream a évolué dans la même direction? | ⚠️ | Modifications custom (WebSocket + ChatMessage) |
| **Documenté?** | Est-ce que c'est bien documenté? | ✅ | Module docstring, fonctions documentées |
| **Testé?** | Est-ce que ça marche vraiment? | ✅ | Actif en production |
| **Dette technique?** | Code propre ou besoin refactor? | ⚠️ | 767 lignes, besoin de vérifier conflits upstream |

**Verdict:** ✅ **GARDER** — Critique pour synchronisation agents

**Priority:** P0  
**Effort:** 2h (merge avec upstream)

---

## 4. Supergateway POC

| Critère | Question | Score | Notes |
|---------|----------|-------|-------|
| **Utilisé?** | Est-ce que c'est activement utilisé? | ✅ | Actif en prod (docker-compose) |
| **Aligné upstream?** | Est-ce que upstream a évolué dans la même direction? | ❌ | Upstream utilise approche différente |
| **Documenté?** | Est-ce que c'est bien documenté? | ⚠️ | Commentaire dans main.py seulement |
| **Testé?** | Est-ce que ça marche vraiment? | ✅ | Healthcheck configuré |
| **Dette technique?** | Code propre ou besoin refactor? | ⚠️ | POC, peut être remplacé par LiteLLM |

**Verdict:** ⚠️ **REFACTORER** — Utile mais peut être remplacé

**Priority:** P1  
**Effort:** 4h (remplacer par LiteLLM MCP Gateway)

---

## 5. Feishu Integrations

| Critère | Question | Score | Notes |
|---------|----------|-------|-------|
| **Utilisé?** | Est-ce que c'est activement utilisé? | ⚠️ | À vérifier (présent mais usage inconnu) |
| **Aligné upstream?** | Est-ce que upstream a évolué dans la même direction? | ✅ | Upstream a aussi Feishu |
| **Documenté?** | Est-ce que c'est bien documenté? | ⚠️ | Code présent, pas de doc externe |
| **Testé?** | Est-ce que ça marche vraiment? | ⚠️ | À tester |
| **Dette technique?** | Code propre ou besoin refactor? | ⚠️ | 51 KB, gros fichier, à auditer |

**Verdict:** ⚠️ **VÉRIFIER** — Besoin de confirmer usage

**Priority:** P2  
**Effort:** 2h (audit + test)

---

## 6. Docker Compose Config

| Critère | Question | Score | Notes |
|---------|----------|-------|-------|
| **Utilisé?** | Est-ce que c'est activement utilisé? | ✅ | Déploiement Coolify |
| **Aligné upstream?** | Est-ce que upstream a évolué dans la même direction? | ⚠️ | Ajouts custom (supergateway, coolify network) |
| **Documenté?** | Est-ce que c'est bien documenté? | ⚠️ | Env vars listées, pas de doc externe |
| **Testé?** | Est-ce que ça marche vraiment? | ✅ | Prod active |
| **Dette technique?** | Code propre ou besoin refactor? | ⚠️ | 3.9 KB, peut être nettoyé |

**Verdict:** ⚠️ **REFACTORER** — Nettoyer post-merge

**Priority:** P1  
**Effort:** 1h (aligner avec upstream)

---

## 7. Backend Custom (main.py, tools.py)

| Critère | Question | Score | Notes |
|---------|----------|-------|-------|
| **Utilisé?** | Est-ce que c'est activement utilisé? | ✅ | Supporte features custom |
| **Aligné upstream?** | Est-ce que upstream a évolué dans la même direction? | ⚠️ | Modifications custom |
| **Documenté?** | Est-ce que c'est bien documenté? | ⚠️ | Docstrings partielles |
| **Testé?** | Est-ce que ça marche vraiment? | ✅ | Prod active |
| **Dette technique?** | Code propre ou besoin refactor? | ⚠️ | Conflits potentiels avec upstream |

**Verdict:** ⚠️ **REFACTORER** — Merge avec upstream requis

**Priority:** P1  
**Effort:** 4-6h (merge manuel + tests)

---

## 8. Documentation Upgrade (temporaire)

| Critère | Question | Score | Notes |
|---------|----------|-------|-------|
| **Utilisé?** | Est-ce que c'est activement utilisé? | ⚠️ | Utile pour merge en cours |
| **Aligné upstream?** | Est-ce que upstream a évolué dans la même direction? | N/A | Interne au fork |
| **Documenté?** | Est-ce que c'est bien documenté? | ✅ | Très détaillé (5 fichiers) |
| **Testé?** | Est-ce que ça marche vraiment? | N/A | Documentation |
| **Dette technique?** | Code propre ou besoin refactor? | N/A | Documentation |

**Verdict:** ❌ **ARCHIVER** — Post-merge, supprimer ou archiver

**Priority:** P2  
**Effort:** 0.5h (archive)

---

## 9. dev_deploy_temp.tar.gz

| Critère | Question | Score | Notes |
|---------|----------|-------|-------|
| **Utilisé?** | Est-ce que c'est activement utilisé? | ❌ | Fichier temporaire |
| **Aligné upstream?** | Est-ce que upstream a évolué dans la même direction? | N/A | Fichier local |
| **Documenté?** | Est-ce que c'est bien documenté? | ❌ | Aucun |
| **Testé?** | Est-ce que ça marche vraiment? | N/A | Fichier archive |
| **Dette technique?** | Code propre ou besoin refactor? | ❌ | 1.1 GB, inutile |

**Verdict:** ❌ **SUPPRIMER** — Fichier temporaire inutile

**Priority:** P0  
**Effort:** 0.01h (`rm dev_deploy_temp.tar.gz`)

---

## 📈 Résumé par Catégorie

### ✅ À Garder (Core Features)

| Feature | Priority | Effort | Justification |
|---------|----------|--------|---------------|
| **AgentMail Integration** | P0 | 0 | Unique, critique pour email |
| **Infisical MCP** | P0 | 0 | Sécurité, gestion secrets |
| **Gateway API Enhanced** | P0 | 2h | Critique pour Clawith Repair |

**Total:** 3 features, 2h effort

---

### ⚠️ À Refactorer

| Feature | Priority | Effort | Action |
|---------|----------|--------|--------|
| **Supergateway** | P1 | 4h | Remplacer par LiteLLM |
| **Docker Compose** | P1 | 1h | Nettoyer post-merge |
| **Backend Custom** | P1 | 4-6h | Merge avec upstream |
| **Feishu** | P2 | 2h | Audit + test usage |

**Total:** 4 features, 11-13h effort

---

### ❌ À Supprimer

| Feature | Priority | Effort | Justification |
|---------|----------|--------|---------------|
| **dev_deploy_temp.tar.gz** | P0 | 0.01h | 1.1 GB, inutile |
| **Documentation upgrade** | P2 | 0.5h | Post-merge, archiver |

**Total:** 2 features, 0.5h effort

---

## 🎯 Effort Total de Cleanup

| Phase | Effort | Délai |
|-------|--------|-------|
| **Immediate (P0)** | 2h | 1 jour |
| **Short-term (P1)** | 11-13h | 2-3 jours |
| **Long-term (P2)** | 2.5h | 1 jour |

**Total:** **15.5-17.5 heures** (~2-3 jours de travail)

---

## 📋 Recommandations

### Priorité absolue (P0)
1. ✅ **Supprimer** `dev_deploy_temp.tar.gz` (1.1 GB)
2. ✅ **Garder** AgentMail, Infisical, Gateway API (core features)

### Court terme (P1)
1. ⚠️ **Merge upstream v1.7.1** (4-6h)
2. ⚠️ **Remplacer Supergateway** par LiteLLM MCP Gateway (4h)
3. ⚠️ **Nettoyer docker-compose.yml** (1h)

### Long terme (P2)
1. ⚠️ **Auditer Feishu** (confirmer usage)
2. ❌ **Archiver documentation upgrade** (post-merge)

---

**Prochain livrable:** CLEANUP_PLAN.md (plan détaillé étape par étape)
