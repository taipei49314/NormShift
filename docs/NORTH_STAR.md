# NormShift 北極星

**Project:** NormShift  
**Positioning:** Semantic Diff & Requirement Lineage for Technical Standards  
**Status:** North Star Charter  
**Date:** 2026-08-07  
**Primary Builder:** Grok 4.5  
**Release Authority:** External reviewer, not the implementing agent

---

## 0. 北極星一句話

> **A standard is not a document. It is a time-varying system of obligations.**
>
> 技術標準不是一份靜態文件，而是一組隨版本演化的義務、禁止、許可、條件、例外與依賴關係。

NormShift 的終局不是把兩份文件做得更漂亮地 diff，而是建立一張可驗證的 **Requirement Lineage Graph**：

- 每一項要求何時出現；
- 曾經要求誰做什麼；
- 強度、極性、範圍、條件與例外如何改變；
- 是否搬移、拆分、合併或被取代；
- 變更影響了哪些相依要求；
- 每個判斷由哪些原文與證據支持；
- 哪些部分仍無法可靠判定。

---

## 1. 最終產品承諾

給定同一技術標準的任意兩個版本，NormShift 應能產生一份 **可重播、可驗證、可追溯且明確表達不確定性** 的演化報告，回答：

1. 哪些規範性要求被新增、刪除或搬移。
2. 哪些要求由建議升級為強制，或由強制放寬為建議／許可。
3. 哪些要求從允許變成禁止，或反向改變。
4. 哪些要求增加或移除了前置條件、例外、適用角色與適用範圍。
5. 哪些句子只是編輯性修改，而沒有改變實作者義務。
6. 哪些要求被拆成多條、由多條合併，或被另一條要求取代。
7. 哪些定義或交叉引用的變化，間接改變了其他要求的意義。
8. 哪些變更具有高實作影響，應優先通知維護者。
9. 哪些配對或分類不足以可靠裁決，必須標示為 `AMBIGUOUS`。
10. 每個結論能否從原始文件快照、來源定位、演算法版本與內容雜湊重新驗證。

終局判準：

> **NormShift 不只指出文字變了，而是證明「實作者被要求做什麼」發生了什麼變化。**

---

## 2. 問題本質

傳統文字 diff 擅長回答：

- 哪些字被新增或刪除；
- 哪些段落被移動；
- 哪些標點或格式不同。

但它無法可靠回答：

- `SHOULD` 改成 `MUST` 是否構成相容性風險；
- `MUST send` 改成 `MUST NOT send` 是否為極性翻轉；
- 一條要求只是換了節次，還是真的被刪除再新增；
- 加入 `unless private mode is active` 是否縮小了義務範圍；
- `client` 改成 `authenticated client` 是否改變適用對象；
- 原文未變，但其引用的定義改變，是否造成隱含語意漂移；
- 規格作者宣稱是 editorial change，實際上是否改變了 normative meaning。

因此 NormShift 的核心對象不是句子，而是 **Requirement Identity、Requirement Instance 與 Change Event**。

---

## 3. 產品邊界

### 3.1 NormShift 是什麼

- 技術標準的規範性要求抽取器。
- 跨版本 requirement alignment engine。
- 義務強度、極性、範圍、條件與例外的變更分類器。
- requirement lineage graph builder。
- 可重播的 evidence ledger 與 verifier。
- 標準版本監控與主動發現系統。
- 公開、可擴充的標準演化 benchmark。

### 3.2 NormShift 不是什麼

- 不是通用文件摘要器。
- 不是法律意見或法規裁決工具。
- 不是合規認證機構。
- 不是「把 PDF 丟給 LLM，讓它說哪裡不同」的包裝器。
- 不是只靠 embedding similarity 的近似搜尋工具。
- 不是聲稱理解任意自然語言的語意神諭。
- 不是自動修改標準或自動修復產品程式碼的工具。
- 不是早期就需要 Dashboard、帳號、SaaS 或大型分散式系統的產品。

---

## 4. 主要使用者

### 標準編輯者

確認新草案是否意外改變規範性含義，並產生 evidence-backed change log。

### 實作者與維護者

快速知道新版本是否增加必做行為、移除舊行為或引入相容性風險。

### 測試與驗證團隊

將 requirement change 轉為需要新增、修改或淘汰的測試範圍。

### 安全、隱私與治理團隊

追蹤禁止事項、例外、資料處理義務與角色適用範圍的演化。

### 研究者與工具作者

研究技術標準如何隨時間變化，並建立可重播的標註語料與演算法基準。

---

## 5. 核心資產：Requirement Lineage Graph

NormShift 最終的護城河不是 CLI，也不是報告版面，而是 **Requirement Lineage Graph，RLG**。

### 5.1 核心節點

- `DocumentSnapshot`
- `Section`
- `Definition`
- `RequirementLineage`
- `RequirementInstance`
- `Actor`
- `Action`
- `Object`
- `Condition`
- `Exception`
- `CrossReference`
- `ChangeEvent`
- `EvidenceSpan`
- `ReviewDecision`

### 5.2 核心關係

- `CONTAINED_IN`
- `DEFINED_BY`
- `APPLIES_TO`
- `REQUIRES`
- `FORBIDS`
- `PERMITS`
- `CONDITIONED_ON`
- `EXCEPT_WHEN`
- `DEPENDS_ON`
- `REFERENCES`
- `SUPERSEDES`
- `MOVED_TO`
- `SPLIT_INTO`
- `MERGED_FROM`
- `CONFLICTS_WITH`
- `EVIDENCED_BY`

### 5.3 身分模型

NormShift 必須分離三種身分：

1. **Snapshot ID**：一份確切文件版本的內容雜湊。
2. **Requirement Instance ID**：某版本中一條要求的確切內容與來源身分。
3. **Requirement Lineage ID**：跨版本持續存在的概念性要求身分。

不得把「文字相似」直接等同於「同一條 requirement」。Lineage 必須由多訊號對齊、證據與信心共同建立。

---

## 6. 規範語意框架

每一個 Requirement Instance 至少要能表示：

```text
actor
modality
polarity
action
object
scope
condition
exception
temporal_constraint
cross_references
source_locator
original_text
normalized_text
confidence
extractor_version
```

### 6.1 Modality

- `MUST`
- `MUST_NOT`
- `SHOULD`
- `SHOULD_NOT`
- `MAY`
- 後續可擴充 `SHALL`、`REQUIRED`、`RECOMMENDED`、`OPTIONAL` 等 profile-specific modality。

### 6.2 變更分類層

#### 文字層

- `UNCHANGED`
- `EDITORIAL`
- `MOVED`

#### 存在層

- `ADDED`
- `REMOVED`
- `SUPERSEDED`

#### 義務層

- `STRENGTHENED`
- `WEAKENED`
- `POLARITY_FLIP`
- `MODALITY_CHANGED`

#### 範圍層

- `ACTOR_CHANGED`
- `OBJECT_CHANGED`
- `SCOPE_EXPANDED`
- `SCOPE_NARROWED`
- `CONDITION_ADDED`
- `CONDITION_REMOVED`
- `EXCEPTION_ADDED`
- `EXCEPTION_REMOVED`

#### 結構層

- `SPLIT`
- `MERGED`
- `RELOCATED_AND_REWRITTEN`

#### 依賴層

- `DEFINITION_CHANGED`
- `REFERENCE_TARGET_CHANGED`
- `DEPENDENCY_CHANGED`
- `CONFLICT_INTRODUCED`
- `CONFLICT_RESOLVED`

#### 不確定層

- `AMBIGUOUS`
- `UNRESOLVED_ALIGNMENT`
- `UNSUPPORTED_CONSTRUCT`

任何不足以支持明確分類的案例，都必須退回不確定 verdict，不得為了提高表面覆蓋率而強迫判斷。

---

## 7. 不可妥協的信任模型

### 7.1 Evidence before interpretation

每個 verdict 必須連回：

- 舊版與新版原文；
- 精確來源位置；
- 文件快照雜湊；
- requirement instance ID；
- alignment score components；
- classification reasons；
- 工具與規則版本。

### 7.2 Deterministic core

M0 至 M4 的正式 correctness path 必須 deterministic。

LLM 日後可以：

- 提出候選 actor/action；
- 協助解釋報告；
- 建議人工複核優先順序。

但 LLM 不得：

- 成為唯一 requirement extractor；
- 成為 alignment authority；
- 成為 final classification authority；
- 靜默改寫 ground truth；
- 在沒有證據時把模糊案例宣稱為確定。

### 7.3 Uncertainty is a product feature

`AMBIGUOUS` 不是失敗，而是可信度機制。系統必須區分：

- 沒有變更；
- 有變更且可分類；
- 很可能有變更但證據不足；
- 無法可靠配對；
- 格式或語言結構暫不支援。

### 7.4 Reproducibility

相同輸入、相同設定、相同版本，必須產生 byte-deterministic 的核心 JSON artifact。

### 7.5 Append-only adjudication

人工複核不得覆寫歷史。任何 override 必須保存：

- 原始機器 verdict；
- 人工 verdict；
- reviewer；
- 理由；
- 時間；
- evidence；
- 規則或模型版本。

---

## 8. 系統架構

```text
Source Adapter
    ↓
Immutable Snapshot Store
    ↓
Structure Normalizer
    ↓
Normative Region Detector
    ↓
Requirement Extractor
    ↓
Semantic Frame Builder
    ↓
Candidate Generator
    ↓
Multi-signal Alignment Engine
    ↓
Change Classifier
    ↓
Dependency / Definition Analyzer
    ↓
Evidence Ledger
    ↓
Verifier
    ↓
JSON / Markdown / SARIF / Feed / Graph Export
```

### 8.1 Source Adapter

負責不同標準來源格式：

- 本地 HTML；
- RFC HTML/XML；
- W3C／WHATWG HTML；
- 後續再支援 Markdown、AsciiDoc、PDF 或其他格式。

Adapter 只負責取得與正規化來源，不得偷偷進行語意裁決。

### 8.2 Immutable Snapshot Store

每份文件必須保存：

- 原始 bytes；
- SHA-256；
- canonical URL 或本地來源；
- fetch metadata；
- content type；
- adapter version；
- normalization version。

### 8.3 Structure Normalizer

處理：

- heading hierarchy；
- section identity；
- anchors；
- lists；
- tables；
- code/example/pre blocks；
- boilerplate；
- normative／informative region；
- generated navigation。

### 8.4 Requirement Extractor

先以 profile-driven deterministic rules 為主：

- token boundaries；
- modality lexicon；
- negation；
- sentence boundary；
- HTML context；
- section semantics；
- code/example exclusion。

### 8.5 Semantic Frame Builder

逐步將 requirement 拆成：

```text
[Actor] [Modality] [Polarity] [Action] [Object]
[Condition] [Exception] [Scope] [Reference]
```

無法可靠抽取的欄位可以為 unknown，但不得虛構。

### 8.6 Alignment Engine

不得只靠單一 fuzzy score。至少綜合：

- normalized text similarity；
- modality compatibility；
- actor/action/object similarity；
- section context；
- anchor／identifier history；
- structural position；
- neighboring requirements；
- cross-reference continuity；
- definition continuity。

必須支援：

- one-to-one；
- one-to-many；
- many-to-one；
- no-match；
- competing candidate ambiguity。

### 8.7 Change Classifier

Classifier 只對已建立的候選 alignment 進行判定，並輸出：

- classification；
- confidence；
- reasons；
- contributing signals；
- contradictory signals；
- unresolved questions。

### 8.8 Evidence Ledger and Verifier

Verifier 必須能重新驗證：

- snapshot hashes；
- artifact schema；
- requirement evidence spans；
- change evidence hashes；
- tool version；
- benchmark identity；
- artifact tampering；
- stale evidence。

---

## 9. 主動發現能力

NormShift 的高階價值不是被動等使用者上傳兩份文件，而是主動觀測：

1. 監控已登記標準是否發布新版本。
2. 取得 immutable snapshot。
3. 自動執行 extraction、alignment、classification 與 verification。
4. 只把具有 normative impact 或高 ambiguity 的變更送入 attention queue。
5. 對相同 requirement lineage 建立時間序列。
6. 發現長期趨勢：要求逐步收緊、例外逐步增加、角色責任轉移或安全要求被弱化。
7. 發現文件聲明與實際變更之間的落差，例如「editorial only」但出現 modality 或 scope change。

這是使用者所追求「AI 不只回答，而是主動發現」的一個受控、可驗證且可落地的垂直領域版本。

---

## 10. 里程碑路線

## M0 — Normative HTML Vertical Slice

### 目標

證明 deterministic semantic diff 可以從本地 HTML 端到端運作。

### 必須完成

- RFC2119 與 WHATWG profile。
- Requirement extraction。
- one-to-one alignment。
- 基本 modality、polarity、condition、exception 分類。
- JSON／Markdown report。
- Artifact verification。
- Immutable synthetic benchmark。
- byte-deterministic output。

### 出口門檻

- 所有固定 adversarial cases 通過。
- tampered report 必須失敗。
- benchmark expected labels 未被調整。
- 只能宣稱 `M0_IMPLEMENTED_PENDING_EXTERNAL_AUDIT`。

---

## M1 — Real Standards Adapters & Provenance

### 目標

從 synthetic fixtures 進入真實標準文件。

### 必須完成

- RFC HTML/XML adapter。
- W3C／WHATWG adapter。
- snapshot metadata、ETag、checksum、canonical source。
- normative／informative region detection。
- boilerplate、navigation、example/code exclusion。
- 真實文件 regression corpus。

### 出口門檻

- 至少三種真實文件家族可重播。
- adapter failure 不得產生假成功 artifact。
- 所有來源都有 immutable provenance。

---

## M2 — Requirement Lineage Graph

### 目標

從單次 diff 升級為跨版本 lineage tracking。

### 必須完成

- persistent lineage ID。
- one-to-many split。
- many-to-one merge。
- moved + rewritten。
- actor/action/object/scope change。
- definitions 與 cross-reference graph。
- ambiguity queue。
- lineage graph export。

### 出口門檻

- 跨三個以上連續版本可保持 requirement identity。
- split／merge 不得退化為大量錯誤 add/remove。
- 每條 lineage 可回溯所有 instance 與 evidence。

---

## M3 — NormShift Observatory

### 目標

讓系統主動監控標準演化。

### 必須完成

- watch list。
- scheduled snapshot acquisition。
- update detection。
- verified diff pipeline。
- attention queue。
- JSON／RSS／GitHub Action／static report 輸出。
- failure isolation 與 retry ledger。

### 出口門檻

- 新版本出現時能自動產生可驗證報告。
- 來源失敗、解析失敗與無變更必須被清楚區分。
- Observatory 不得因抓取成功就宣稱語意分析成功。

---

## M4 — Public Benchmark & Evaluation Standard

### 目標

把 NormShift 從工具變成一個可公開比較的研究基準。

### 必須完成

- 人工標註 benchmark。
- extraction、alignment、classification 分離評分。
- adversarial corpus。
- inter-annotator disagreement 記錄。
- benchmark versioning 與 freeze policy。
- baseline implementations。

### 核心指標

- extraction precision／recall；
- alignment precision／recall／F1；
- classification macro-F1；
- false substantive-change rate；
- false no-change rate；
- ambiguity calibration；
- evidence completeness；
- deterministic replay rate。

### 出口門檻

- 所有公開指標可由第三方 clean clone 重跑。
- benchmark 變更必須留下版本與理由。
- 不得只公布單一總分掩蓋弱點。

---

## M5 — Implementation Impact Mapping

### 目標

將 requirement change 連到實作者真正需要處理的資產。

### 可擴充能力

- Requirement ↔ test mapping。
- Requirement ↔ code/module mapping。
- Requirement ↔ documentation mapping。
- change impact checklist。
- stale test detection。
- implementation evidence gap。

### 邊界

NormShift 只提供 impact evidence，不直接宣稱產品合規或程式碼已正確修復。

---

## M6 — Standards Time Graph

### 目標

形成技術標準的公開時間圖譜與研究平台。

### 終局能力

- 查詢某 requirement 的完整生命史。
- 比較不同標準對相似義務的演化。
- 發現定義漂移、規範衝突與責任轉移。
- 追蹤安全、隱私、相容性要求的長期趨勢。
- 產生 evidence-backed release impact brief。
- 對高風險變更進行主動提醒。

---

## 11. 評價標準

NormShift 的成功不以程式碼行數、支援文件數或 UI 華麗程度衡量。

### 第一優先：錯誤的 substantive verdict 必須極低

錯把 editorial change 判成 normative change，會造成大量噪音；錯把 normative change 判成 editorial，則可能漏掉真正風險。

### 第二優先：證據完整度

每個 verdict 必須能回到來源，任何無 evidence 的結論都只是提示，不是正式輸出。

### 第三優先：alignment 穩定性

Requirement identity 是整個時間圖譜的地基。錯誤配對比無法配對更危險。

### 第四優先：不確定性校準

高 confidence 必須真的比低 confidence 更可靠。系統不能把所有案例都假裝成確定。

### 第五優先：可重播性

第三方必須能以相同快照、版本與設定重新得到相同 artifact。

---

## 12. 主要威脅模型

NormShift 必須持續對抗：

- `mustard` 等 token boundary 誤命中；
- `is not required to` 被誤判為 `MUST_NOT`；
- normative 字詞出現在 code、example、quote 或歷史說明；
- section renumbering 被誤判為 add/remove；
- 同義改寫造成錯誤 deletion；
- 高度相似 requirement 交叉配對；
- 一條 requirement 拆成多條；
- 多條 requirement 合併；
- modality 不變但 actor、scope、condition 或 exception 改變；
- 原文不變但 definition 或 cross-reference target 改變；
- normative/informative section 判斷錯誤；
- hidden HTML、Unicode、entity、generated content 造成解析差異；
- benchmark overfitting；
- expected label 被施工 Agent 偷改；
- tests 存在但未執行；
- evidence bundle 對應舊 commit；
- report 被手動修改後仍通過 verify；
- AI 以流暢說明掩蓋低信心或無證據結果。

每一個已知 failure mode 都應成為：

1. 固定 fixture；
2. regression test；
3. threat-model entry；
4. benchmark case，若適用。

---

## 13. 開源護城河

NormShift 真正的長期優勢應由以下資產累積，而不是靠品牌敘事：

1. 高品質、可公開重跑的 requirement-change benchmark。
2. 多標準來源 adapter 與 normalization know-how。
3. 跨版本 requirement lineage corpus。
4. 可解釋的 alignment 與 classification signals。
5. evidence ledger、tamper detection 與 replay workflow。
6. ambiguity handling 與人工 adjudication 資料。
7. 標準演化時間圖譜。

任何競爭者都可以做一個文字 diff UI；更難複製的是經過長期驗證的 lineage、benchmark 與 provenance corpus。

---

## 14. 治理規則

### 14.1 實作者沒有完成宣告權

Grok 可以：

- 實作；
- 測試；
- 建立 evidence；
- 回報已執行命令與結果。

Grok 不可以自行宣稱：

- production-ready；
- release-ready；
- semantically correct；
- fully verified；
- complete。

每個里程碑最高只能到：

```text
M*_IMPLEMENTED_PENDING_EXTERNAL_AUDIT
```

### 14.2 Claims 必須被登記

`CLAIMS.md` 中每一項公開宣稱必須包含：

- claim；
- scope；
- supporting evidence；
- unsupported boundary；
- last verified commit；
- reviewer status。

### 14.3 Benchmark 不得由實作方便性控制

- expected labels 必須 freeze；
- 修改必須留下理由與審查紀錄；
- 施工 Agent 不得因測試失敗而降低標準；
- 不得刪除、skip 或弱化 adversarial cases。

### 14.4 每個里程碑必須封存 evidence bundle

至少包含：

- commit SHA；
- dependency lock hash；
- exact commands；
- exit codes；
- test logs；
- benchmark metrics；
- generated artifacts；
- artifact hashes；
- known failures；
- unresolved risks。

---

## 15. Grok 自主施工循環

每一輪只允許一個主要假設與一個可驗證增量：

```text
OBJECTIVE
  ↓
HYPOTHESIS
  ↓
IMPLEMENTATION
  ↓
NARROW TEST
  ↓
FULL GATE
  ↓
EVIDENCE UPDATE
  ↓
RISK / NEXT ACTION
```

`MISSION_STATE.json` 必須持續記錄：

- current_objective；
- current_hypothesis；
- status；
- last_verified_commit；
- commands_run；
- verified_artifacts；
- known_failures；
- unresolved_risks；
- next_action。

不得連續建立大量 placeholder architecture。每個抽象層都必須由真實 fixture、執行路徑與驗證案例拉動。

---

## 16. 第一施工序列

Grok 現在不應直接嘗試完成整個北極星，只應按以下順序推進 M0：

1. 建立最小 repository、CLI 與 immutable synthetic fixtures。
2. 完成 HTML 結構正規化與 code/example exclusion。
3. 完成 RFC2119／WHATWG modality extraction。
4. 建立 Requirement schema 與 deterministic IDs。
5. 建立最小 one-to-one alignment engine，公開 score components。
6. 完成核心 modality、polarity、condition、exception classifier。
7. 產生 evidence-linked JSON 與 Markdown report。
8. 建立 verifier 與 tamper test。
9. 建立 immutable benchmark runner。
10. 執行完整 clean-clone gate，封存 M0 evidence bundle。
11. 停止擴張，交給外部審查。

在 M0 通過前，不得投入 Dashboard、crawler、database、LLM 或大規模 adapter。

---

## 17. 終局示例

假設某標準在三個版本中發生：

```text
v1: A client SHOULD retain the token for 24 hours.
v2: An authenticated client MUST retain the token for 24 hours.
v3: An authenticated client MUST retain the token unless private mode is active.
```

NormShift 最終應能輸出：

```text
Lineage: RQ-0042

v1 → v2
- Classification: STRENGTHENED
- Actor scope: client → authenticated client
- Modality: SHOULD → MUST
- Impact: mandatory behavior introduced for a narrower actor class

v2 → v3
- Classification: EXCEPTION_ADDED
- Exception: private mode is active
- Impact: mandatory behavior no longer applies under the new exception

Evidence
- exact old/new source spans
- snapshot SHA-256
- alignment scores
- rule versions
- verifier status
```

它不只說哪幾個字不同，而是重建整條義務生命史。

---

## 18. 最終北極星宣言

> **Given any two snapshots of a technical standard, NormShift should produce a reproducible, evidence-linked account of every obligation that appeared, disappeared, moved, strengthened, weakened, changed polarity, changed scope, gained or lost conditions or exceptions, split, merged, became indirectly affected by definitions, or remained genuinely ambiguous — and prove why.**

中文版本：

> **給定任意兩個技術標準快照，NormShift 必須能以可重播、可追溯的證據，說明每一項義務如何出現、消失、搬移、增強、弱化、翻轉、改變範圍、增加或移除條件與例外、拆分、合併，或因定義與依賴而受到間接影響；對無法可靠判斷的部分，則誠實保留不確定性。**

這就是 NormShift 的北極星。所有功能、架構、模型與介面，都必須服務於這個能力；不能服務它的東西，現在就不該做。
