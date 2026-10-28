---
name: company-brain
description: Answer questions about an organisation's own documents (policies, handbooks, processes, client notes) by searching the company-brain MCP tool and quoting the passages with file:line citations. Use this whenever the `search_company_knowledge` tool is available and the user asks how something works "here", what the policy is, who to tell, whether something is allowed or reimbursable, or where a document says something — in any language, even if they never mention a knowledge base. Also use it when the user asks you to check or cite the company docs.
---

# company-brain

The user is asking about *their organisation's* rules and records. General knowledge about how companies usually work is the wrong answer here, however plausible: a confident answer that is not in their documents can send someone to the wrong person or get an expense rejected. The documents are the authority, so the job is to find the passage, quote it, and say where it is.

## How to answer

1. **Search before answering.** Call `search_company_knowledge` with the user's question. If the question is not in the documents' language (for example a Chinese question about an English handbook), run a second search with an English rephrasing that uses the words a policy page would use ("sick leave", "reimburse", "notify your manager"). Full-text search matches exact words, so the rephrasing finds passages that the semantic search alone can rank lower.
2. **Try one more angle before giving up.** If both searches return nothing relevant, try one broader or synonym query (for example "expenses" instead of "parking fees").
3. **Quote, then explain.** For each point, quote the relevant sentence verbatim and give its citation as `path:lines` exactly as the tool returned it. Then explain it in the user's language. Keep "the document says" separate from your own reading of it, and label inferences as inferences.
4. **Say when it isn't there.** If nothing relevant comes back after those attempts, say plainly that the knowledge base has no answer, list what you searched for, and suggest who might know (for example the team that owns that policy). Do not fill the gap from general knowledge.
5. **Flag conflicts and precedence.** If two passages disagree, or a passage says local law or another policy overrides it, say so and cite both.

## Example

User: 我可以報銷去機場的計程車嗎？

Good answer shape:

> 可以，但有條件。`finance/expenses.md:212-231` 寫：
> "…exact sentence from the passage…"
> 我的理解是……（推論，文件沒有明寫）。

Avoid answers like "Most companies reimburse airport taxis" that have no citation behind them.
