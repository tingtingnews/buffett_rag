# ValueOS Investment Knowledge Base — RAG Source File

> **Purpose:** Structured knowledge extraction for building a Retrieval-Augmented Generation (RAG) system.
> **Design note for the RAG builder:** Every section below is written as a *self-contained chunk*. Each one repeats its key entities (ticker names, numbers, dates) so it remains retrievable and meaningful in isolation. Split on the `##` and `###` headers. Recommended chunk size: one `###` block each (~200–500 tokens). Do not strip the metadata lines — they aid filtering.
> **As-of date:** June 17, 2026. Time-sensitive figures are dated inline. Prices change; canonical IVs and methodology are stable.
> **Disclaimer to propagate:** This is an analytical framework, not investment advice. The author is not a licensed financial or tax advisor.

---

## 1. INVESTOR PROFILE

### 1.1 Who the investor is
`tags: profile, goals, context`
The investor ("Ting") is a Taiwanese value investor with a semiconductor-industry background, which gives a genuine analytical edge on TSMC. Investment philosophy is strict Buffett/Munger value investing: owner-earnings DCF, margin of safety, moat durability, ROIC as a quality screen. The investor is anti-FOMO, AI-skeptical about hype, long-term oriented, and explicitly does not want to day-trade or learn technical trading. Possible future US relocation but the green card timeline is uncertain as of mid-2026.

### 1.2 Financial goals
`tags: profile, goals, targets`
Primary goal: a $1.5M portfolio generating passive income, targeted for approximately 2045. Income milestones: $2,000/month within 10 years, $5,000/month within 15 years (at 4% withdrawal). Target weighted annual return: 12–15% (base case 14.9%). Monthly contributions: $1,000/month through December 2026, rising to $1,200–$1,500/month from 2027 as US income is established. The single most powerful lever identified: raising monthly contributions from $1,000 to $1,500 adds roughly $388,000 to the 2041 outcome.

### 1.3 Brokerages and accounts
`tags: profile, tools, accounts`
US brokerage: Charles Schwab / Firstrade (account holds US-listed equities). Taiwan brokerage: holds TSMC ordinary shares (ticker 2330) and Taiwan ETFs (0050, 0056). Data sources used: Gurufocus (TTM FCF), SEC EDGAR (8-K, 10-Q, 6-K filings), Seeking Alpha (cross-reference), and brokerage app screenshots as authoritative price source. App screenshots taken within ~4 hours of US market close may show stale prior-day data — always reconcile against the timestamp.

---

## 2. CANONICAL INTRINSIC VALUES (most current)

### 2.1 Canonical IV table — June 2026
`tags: IV, canonical, valuation, core`
These are the authoritative intrinsic values. Always use these before generating any report; never use older manually-stated estimates if these exist.
- **MCO (Moody's):** IV = $519 (base raised from the strict-reconciled $462 to $519 in a deliberate July 2026 decision to use g1=15% instead of 13%). Inputs: g1=15%, g2=11%, terminal=3.5%, discount rate=9.5%. Owner earnings $2,533M. Note: 15% is still a conscious haircut below MCO's ~19% historical EPS CAGR — it is a chosen growth assumption, NOT a guidance multiplier. The earlier $560 carried a ~1.21× guidance-inflation that was removed; $519 comes from a clean DCF at the higher-but-still-conservative growth rate.
- **V (Visa):** IV = $338 (reconciled down from guidance-inflated $400). Inputs: g1=13%, g2=9%, terminal=4%, discount rate=10%. Owner earnings $21,821M incl. MDL add-back.
- **TSM (TSMC ADR):** IV = $620 (raised from $510 in June 2026 based on Q1 2026 actuals). Inputs: g1=20%, g2=12%, terminal=4%, discount rate=11%. Owner earnings per ADR ≈ $19.19.
- **MSFT (Microsoft):** IV = $445 (revised down from $520 in July 2026 using clean FY2026 actuals). Inputs: g1=15%, g2=10%, terminal=3.5%, discount rate=10.5%, owner earnings ≈ $111.5B, OE/share ≈ $15.01. Honest range $255 (conservative) to $525 (optimistic); central case $445. At price ~$390 = 87.6¢ per dollar (accumulate zone).
- **AVGO (Broadcom):** IV ≈ $309 (raised from $230 in June 2026 based on Q2 FY2026 FCF of $10.262B). Inputs: g1=20%, g2=12%, discount rate=10–11%.

### 2.2 TSMC IV update rationale (June 2026)
`tags: IV, TSMC, update, valuation`
TSMC IV was raised from $510 to $620 in June 2026. Reason: Q1 2026 actuals (filed via SEC 6-K, April 16 2026) showed net income of NT$572.48B (US$17.55B), up 58.3% year-over-year, with EPS of NT$22.08 (US$3.49/ADR), gross margin 66.2%, net margin 50.5%, ROE 40.5%. Q1 2026 free cash flow was NT$348.21B (~$10.98B/quarter, ~$43.9B annualized). This is a structurally higher earnings base than the old FY2025 blended estimate of $57.5B. Updated owner earnings ≈ $99.5B total, ~$19.19/ADR. Net cash $106B confirmed (+$14.08/ADR). At ADR price ~$421, this gives 67.9¢ per dollar — the cheapest position in the portfolio by IV%.

### 2.3 AVGO IV update rationale (June 2026)
`tags: IV, AVGO, Broadcom, update, valuation`
AVGO IV was raised from $230 to ~$309 in June 2026. Reason: Q2 FY2026 results (quarter ended May 3 2026) showed revenue $22.187B, adjusted EBITDA $15.244B, and free cash flow $10.262B for the quarter. Annualized owner earnings ≈ $41B. With ~4.7B shares, OE/share ≈ $8.73. DCF (g1=20%, g2=12%, terminal=4%, discount 11%, minus net debt ~$13/share) gives IV ≈ $309. At price ~$385, AVGO is at 124.8¢ per dollar — still above intrinsic value, still under the "zero new capital" rule. The gap narrowed from 180¢ (May) to 125¢ (June).

### 2.4 MSFT IV confirmation (June 2026)
`tags: IV, MSFT, Microsoft, valuation`
MSFT IV revised to $445 (July 29 2026, from Q4 FY2026 actuals — down from the earlier $520). Full-year FY2026: revenue $331B, operating income $155B, Azure grew 43% (beating 39–40% guidance) and crossed $100B annual for the first time (+41% full year), Copilot >30M paid seats. Q4 revenue $90.01B (+17.8%), reported EPS $4.74 — but that EPS included a one-time $3.2B Anthropic investment gain plus low VRP costs, which must be stripped for the IV. Clean earnings base: operating income $155B × (1−18% tax) ≈ $127B net income. Owner earnings = $127B + $45B D&A − $47.5B maintenance capex (25% of $190B) − $13B SBC = $111.5B; OE/share $15.01. Two-stage DCF (g1=15%, g2=10%, terminal 3.5%, discount 10.5%) plus $37B net cash gives IV ≈ $445. The revision is downward not because the business weakened (it strengthened — Azure 43%) but because the prior $520 rested on an inflated earnings base. Azure at 43% for two consecutive quarters confirms the g1=15% assumption. FY2027 capex guided up to ~$175–260B (partly an accounting reclassification) — the buildout is accelerating, not slowing.

---

## 3. THE VALUATION METHODOLOGY

### 3.1 Owner Earnings formula
`tags: methodology, formula, owner-earnings, Buffett`
Owner Earnings (Buffett's 1986 definition) = Net Income + Depreciation & Amortization − maintenance capital expenditures − Stock-Based Compensation + growth-capex add-back. This differs from website "free cash flow" which deducts ALL capex. Buffett deducts only maintenance capex; growth capex (new fabs, new data centers) is investment in future earnings, not a cost. Growth-capex add-back percentages used: MSFT 75%, TSMC 75%, Visa 0%, Moody's 0%. This single assumption is the most judgment-dependent input in the model.

### 3.2 Two-stage DCF structure
`tags: methodology, formula, DCF, valuation`
Intrinsic value = present value of all future owner earnings, computed as: (1) Years 1–5 at high growth rate g1, discounted. (2) Years 6–10 at moderate growth rate g2, discounted. (3) Terminal value = Year-11 earnings ÷ (discount rate − terminal growth rate), then discounted back 10 years. (4) Sum the three present values to get enterprise value. (5) Add net cash or subtract net debt. (6) Divide by diluted shares outstanding to get IV per share. Graham formula and simple two-stage DCF were tried and rejected in favor of this three-stage owner-earnings approach.

### 3.3 The cardinal data rule
`tags: methodology, rule, data-integrity`
Use trailing-twelve-months (TTM) actual figures from SEC filings (10-K, 10-Q, 8-K, 6-K) only. NEVER use management guidance or analyst estimates in the IV calculation. Management sandbags guidance (guides low, beats) so using guidance understates earning power. Also, guidance is 12-month while the DCF is 10-year — methodologically inconsistent. This rule corrected MCO from $575 to $560 (removed a 1.085 guidance multiplier) and V from $415 to $400 (removed a 1.125 guidance multiplier).

### 3.4 The margin-of-safety / cents-per-dollar framework
`tags: methodology, framework, margin-of-safety, buy-signal, core`
Every position is evaluated as cents paid per $1 of intrinsic value: Margin of Safety = current price ÷ intrinsic value. Zones: ≤70¢ = ideal (buy aggressively); ≤75¢ = good; ≤80¢ = acceptable (buy normally); 80–95¢ = accumulate cautiously; 95–100¢ = hold, do not add; >100¢ = do not buy; >120¢ = consider trimming. This is the single most-used number in the system. A falling price on an unchanged business moves a stock toward the buy zone — it is an opportunity signal, not a warning.

### 3.5 Probability-weighted expected return
`tags: methodology, formula, expected-return, risk`
Each stock's return is weighted by scenario probabilities to capture downside risk, not just upside. As of July 2026: MCO ≈ 13.1%, V ≈ 11.8%, MSFT ≈ 8–9% (raised after $627B RPO and two consecutive Azure quarters ≥40% lifted the base-case probability). MSFT's number remains below its bull case because a conservative scenario exists where the growth-capex add-back is only partly justified and IV falls toward ~$255 — that wide distribution drags the weighted average down. The July 2026 IV revision to $445 (from $520) reflects a cleaner earnings base, not a thesis change. MCO and V have narrow outcome distributions (mild bad cases); MSFT has a wide distribution, which is why its discount rate is 10.5% not 9.5%.

### 3.6 Weighted portfolio return
`tags: methodology, formula, portfolio, return`
Weighted portfolio return = Σ (position weight × expected return). As of May 2026 the portfolio computed to ~14.37% including cash/SGOV drag, rising to ~14.9% as idle cash and SGOV are deployed into MCO. Per-position expected returns used: TSMC 25%, VOO 12%, MCO 15%, V 15%, MSFT 14%, SCHD 11%, AVGO 18%, Taiwan ETFs 10%, SGOV 4.3%, cash 0%.

---

## 4. PORTFOLIO STATE

### 4.1 Confirmed portfolio — May/June 2026
`tags: portfolio, holdings, state`
Total portfolio ≈ $80,352 across three account groups. US Schwab/Firstrade (~$59,257): VOO 37.16 shares, MCO 17.12 shares, MSFT 13.42 shares, SCHD 188.29 shares, SGOV 30.40 shares, V 12.55 shares, AVGO 9.23 shares. Taiwan Stock Exchange: TSMC (2330) 247 odd-lot shares (~$16,095). Taiwan ETFs: 0050 + 0056 combined (~$5,000). Cash/buying power varied $4,041–$6,843 across the period.

### 4.2 Confirmed trade — May 20, 2026
`tags: portfolio, trade, execution`
Executed via Firstrade on May 20, 2026: MCO 3.15 shares at $432.20 ($1,361.43); VOO 1.30 shares at $676.42 ($879.35); V 1.70 shares at $330.09 ($561.15). Total deployed $2,801.93. MCO entry at $432.20 = 77.2¢ per dollar of the then-canonical IV $560 (later reconciled: $462 strict, $519 at chosen g1=15%), inside the ideal zone at the time. The MCO purchase used the Moody's US credit downgrade selloff as the buying opportunity.

### 4.3 Lump sums cancelled
`tags: portfolio, decision, correction`
Two previously-planned lump sums were CANCELLED and removed from all projections: (1) an October 2026 $10,000 deployment, and (2) an $80,000 US-arrival deployment fund. All trajectory models start from the confirmed ~$80,352 base with monthly contributions only — no windfalls assumed. This is a firm correction; do not reintroduce these into any projection.

### 4.4 Monthly allocation framework
`tags: portfolio, allocation, monthly, rules`
Each month: deploy $300 into VOO unconditionally (no price check, no exceptions — the foundation). Allocate the remaining ~$700 across MCO/V/MSFT by cents-per-dollar, giving the largest slice to whichever is cheapest that month. Default split when all are 80–85¢: VOO $300, MCO $350, V $200, MSFT $150. Adjust toward whichever individual stock is in the deepest buy zone. Special rule: if any stock falls 15%+ in a month, double that stock's allocation if cash is available. The price signal, not the calendar, triggers action — deploying early when a stock hits the ideal zone is consistent with the framework.

---

## 5. STOCK THESES

### 5.1 MCO — Moody's Corporation
`tags: stock, MCO, Moodys, thesis`
Business: bond credit-rating duopoly (Moody's + S&P ≈ 80% market share); legally and practically irreplaceable. IV $519 (g1=15%, g2=11%, dr=9.5% — base deliberately raised from strict-reconciled $462 by choosing 15% growth, still below the ~19% historical CAGR). Owner earnings ≈ $2,533M from TTM actuals (TTM net income $2,459M). 176M diluted shares, shrinking via buybacks. Probability-weighted return 13.1% — highest in the portfolio. Paradox: credit downgrade events (like the May 16 2026 Moody's US downgrade from Aaa to Aa1) INCREASE MCO revenue because more bonds need restructuring and re-rating. Immune to or benefits from financial stress and Dalio's debt-cycle scenario. Highest IV certainty of all positions. Scenario range: bear (g1=11%) $364, base (g1=15%) $519, bull (g1=18%) $744.

### 5.2 V — Visa Inc.
`tags: stock, V, Visa, thesis`
Business: global payment network with a near-unassailable network-effect moat; takes a percentage of transaction value, carries no credit risk. IV $338 (g1=13%, g2=9%, dr=10% — reconciled down from the guidance-inflated $400 by removing a ~1.18× multiplier; clean DCF at strict growth). Owner earnings ≈ $21,821M (FY2025), which includes a confirmed one-time MDL litigation add-back of $2,073M. ~1,916M diluted shares, reduced by a $7.9B Q2 buyback. Catalysts: FIFA World Cup (began June 15 2026) boosts cross-border transaction volume 20–30%; agentic-AI autonomous purchases flow through Visa rails. Inflation-protected (earns % of nominal transaction value). Scenario range: bear (g1=10%) $226, base (g1=13%) $338, bull (g1=16%) $451. Note: V has become the most expensive quality name by IV% — even the bull case only reaches 0.81x at ~$365.

### 5.3 TSM — TSMC
`tags: stock, TSM, TSMC, thesis, semiconductor`
Business: manufactures ~90% of the world's most advanced chips; the "arms dealer" that supplies Nvidia, AMD, Apple, Broadcom, Google, and Cerebras simultaneously — competition among chip designers means more TSMC orders. IV $620 (raised June 2026; g1=20%, g2=12%, terminal=4%, dr=11%). The 11% discount rate (highest in the portfolio) prices in ~10–12% probability of Taiwan geopolitical risk over 10 years. Owner earnings ~$19.19/ADR. Net cash $106B. The investor holds 247 TSMC ordinary shares (2330) on the Taiwan exchange, planned for conversion to TSM ADR by 2028.

### 5.4 MSFT — Microsoft
`tags: stock, MSFT, Microsoft, thesis`
Business: Azure cloud + enterprise software + AI. IV $445 (revised July 2026; g1=15%, dr=10.5%). The 10.5% discount rate carries a premium for the $190B/year capex uncertainty. Owner earnings ≈ $111.5B, OE/share ≈ $15.01, depends on a 75% growth-capex add-back. Sensitivity is the defining feature: conservative assumptions (50% add-back, 13% growth) give ~$255; optimistic (75% add-back, 17% growth) give ~$525; central case $445. Confidence in the growth assumption raised by Azure hitting 43% in Q4 FY2026 (two consecutive quarters ≥40%) and $627B RPO. The Azure growth rate is the live monitoring trigger. Per the trigger table, Azure ≥40% sets the August+ monthly allocation to the top tier ($250/mo).

### 5.5 AVGO — Broadcom
`tags: stock, AVGO, Broadcom, thesis`
Business: custom AI chips (ASICs for Google, Meta, Apple) plus networking switches plus VMware infrastructure software. IV ≈ $309 (raised June 2026). Q2 FY2026: revenue $22.187B, AI semiconductor revenue $10.8B (+143% YoY, ~49% of revenue), FCF $10.262B, AI bookings >$30B. CEO Hock Tan explained that Q3 gross margin guided down to ~74% reflects product mix (lower-margin AI chips growing as a share) not structural margin decline. Rule: HOLD existing 9.23-share position (+30%); ZERO new capital while price is above ~$280 (above 100¢ per dollar). At ~$385 = 124.8¢.

### 5.6 VOO — Vanguard S&P 500 ETF
`tags: stock, VOO, index, foundation`
The unconditional foundation. Buy $300/month always, no IV check, no exceptions. Reflects Buffett's own estate instruction: "Put 90% in a very low-cost S&P 500 index fund." VOO-only at 10.5%/year reaches ~$745k by 2041 from the current base; the active framework at 14.9% reaches ~$936k — the ~4.4% annual edge compounds to roughly $191k more wealth over 15 years. Provides diversified recovery exposure when individual-stock bubbles deflate.

### 5.7 SCHD, SGOV, Taiwan ETFs
`tags: stock, SCHD, SGOV, 0050, 0056, holdings`
SCHD (Schwab US Dividend Equity ETF): 188.29 shares, ~11%/yr expected, 3–4% yield. Hold; note that as a non-US-resident the 30% dividend withholding makes SCHD relatively tax-inefficient. SGOV (iShares T-Bill ETF): 30.40 shares, 4.3%/yr — flagged URGENT SELL; redeploy into MCO at ~77¢. 0050 (Taiwan's top-50 index ETF, TSMC ~45% weight, ~10–12%/yr): hold. 0056 (Taiwan high-dividend ETF, ~8–10%/yr, 5–6% yield): hold. Taiwan ETFs total ~$5,000 and provide NT-dollar diversification at a small ~0.3% drag on weighted return.

### 5.8 Watch-list / rejected: Cerebras and SpaceX
`tags: stock, Cerebras, SpaceX, rejected, watch`
Cerebras (IPO May 2026, +68%): wafer-scale AI chips (WSE-3, 4 trillion transistors, 58× larger than Nvidia B200), faster for inference. A TSMC customer (manufactured on TSMC 5nm) — so ZERO threat to TSMC, partial threat to Nvidia's inference share only. Pre-profit, so no calculable IV — cannot invest under the framework; watch only. SpaceX (IPO June 2026 at $135/share, ~$1.77T valuation, ticker SPCX): losing ~$4.94B/year, deeply negative owner earnings, Morningstar fair value ~$780B. At ~480–810¢ per dollar of conservative value. Fails every Buffett filter. REJECTED — not in portfolio.

---

## 6. DECISION RULES

### 6.1 Never sell on price decline alone
`tags: rule, sell-discipline, behavior`
Sell only when the business thesis breaks — never because the price fell. Test before selling: did the business change (not the price)? Is the moat intact? Is management still allocating capital well? Is owner-earnings growth still at or above the conservative assumption? Three "yes" answers = hold and keep buying. A price decline with an unchanged business is a discount, not a warning. Historical evidence: 68% of investors who sold in the 2008 crash never reinvested before the recovery, locking in permanent losses.

### 6.2 Never use management guidance in IV; never change assumptions on one quarter
`tags: rule, methodology, discipline`
Growth-rate assumptions change only when the business fundamentally and durably changes — not every quarter. One weak Azure quarter is noise; two-to-three consecutive weak quarters with no recovery thesis is signal. Example trigger: three consecutive quarters of Azure below 30% would justify cutting MSFT's g1 from 15% to 12%.

### 6.3 Concentration limit
`tags: rule, concentration, risk`
No single individual stock above 30% of total portfolio. (VOO above 30% is acceptable because it is itself 500 companies.) TSMC was ~20% in mid-2026 — watch as it grows. When a position approaches 30%, stop adding new contributions to it and let other positions rebalance it naturally. Rationale: even Buffett has thesis failures (Kraft Heinz); concentration makes a single error catastrophic rather than survivable.

### 6.4 Do not hold cash to time the market
`tags: rule, market-timing, behavior`
Continue monthly contributions through all market conditions. Expected benefit of waiting for a crash (~4.6%) roughly equals the expected cost of missing a rally (~4.2%), netting near zero but with far higher emotional cost. Lump-sum investing beat 12-month dollar-cost-averaging in 68% of rolling 10-year periods (Vanguard 2012). Respond to price signals (the 15%-drop double-up rule), not to predictions about timing.

### 6.5 AVGO zero-new-capital rule
`tags: rule, AVGO, position`
Hold the existing AVGO position; deploy zero new capital while the price is above ~$280 (above ~100¢ per dollar of IV ~$309). Reassess only if AVGO corrects toward $280–300 or after a quarterly earnings update changes the IV.

### 6.6 Sell tax-inefficient positions before citizenship/residency events
`tags: rule, tax, sell-discipline`
Sell low-returning or tax-inefficient positions (previously JEPI, JEPQ, QQQ; currently SGOV) before any citizenship or residency change. SGOV at 4.3% has a large opportunity cost (~$328/year on $3,057) versus deploying into MCO at 15% expected return in the ideal zone.

---

## 7. MACRO CONTEXT (dated; may age)

### 7.1 Moody's US downgrade — May 16, 2026
`tags: macro, MCO, downgrade, dated`
Moody's downgraded US sovereign credit from Aaa to Aa1 on May 16, 2026 — the first time all three major agencies rate the US below top grade (S&P 2011, Fitch 2023, Moody's 2026). Markets fell ~1% then recovered same-day. Historical pattern: the S&P 500 rose ~20% in the year following both the 2011 and 2023 downgrades. The downgrade is paradoxically bullish for MCO's business (more rating events). MCO stock fell on fear, creating the ideal-zone entry.

### 7.2 AI-bubble debate — PTJ, Dalio, Keen
`tags: macro, AI-bubble, risk, dated`
Paul Tudor Jones (mid-2026): AI bull market has "another year or two" then possible "breathtaking corrections" — but he is a 15-month macro trader still buying AI stocks; this does not govern a 15-year plan. Ray Dalio / Bridgewater (June 3 2026): the AI bubble will "eventually" burst via a debt/liquidity mechanism (forced conversion of paper wealth to money), not via the technology failing; many companies will vanish while AI keeps transforming the economy. Dalio gave no specific probability; a "75% in 2026" figure circulating came from an AI chatbot trained on his books, NOT from Dalio. Steve Keen: AI capex-to-revenue is ~5:1 ($720B spend vs ~$100B revenue), which he calls unsustainable.

### 7.3 Honest bubble-burst probability estimates
`tags: macro, AI-bubble, probability, risk`
Definitions matter. Pure AI-speculation stocks (Nvidia, Palantir, Tesla, AVGO at peak prices) crashing 50%+ within 3 years: ~55–65%. Nasdaq falling 30%+: ~25–35%. S&P 500 / VOO falling 30%+: ~10–15%. AI proving economically worthless: <2% (ruled out by existing revenue — MSFT $37B annualized AI revenue, TSMC +58% net income). MCO and V are immune to or benefit from the financial-structure risk Dalio describes; TSMC is partially exposed via Taiwan export risk (already in the 11% discount rate).

### 7.4 TSMC $1.5T chip-market forecast — May 2026
`tags: macro, TSMC, forecast, dated`
TSMC raised its global semiconductor market forecast to $1.5 trillion by 2030 (from $1T), with AI/HPC at 55% = $825B. Independent cross-checks: McKinsey base $1.6T, McKinsey bull $1.8T, ASML (equipment-based, conservative) $1.05T. Scenario mapping for TSM: 50% realization → ADR ~$430; 75% realization (base case, ~55% probability) → ADR ~$570–620; 100% realization → ADR ~$720. The 75% case aligns with the Q1 2026 trajectory.

### 7.5 Taiwan geopolitics and the silicon shield
`tags: macro, Taiwan, geopolitics, TSMC, risk`
TSMC's value is its ~73,000 engineers and accumulated process knowledge, not its buildings. In a forced-invasion scenario (~8–12% over 15 years) US GDP impact is estimated −5 to −8% year 1; TSM effectively worthless short-term. In a voluntary-unification scenario (~3–5%) China would get empty fabs while the US offers TSMC engineers expedited green cards — the people are the moat. Status quo (~85–90%) is most likely; TSMC's Arizona fabs (3nm by 2027, 2nm by ~2029) gradually reduce the strategic incentive to attack. Personal mitigation: convert TSMC ordinary shares to TSM ADR (US-regulated, USD-denominated) by 2028.

### 7.6 Goldman margin-inflection and MSFT RPO
`tags: macro, MSFT, AI-economics, dated`
Goldman (1H 2026): LLM token prices have stabilized while compute costs keep falling 60–70%/year, so AI margins expand automatically with each hardware generation — bullish for Azure unit economics. Microsoft RPO (remaining performance obligations, signed-but-unrecognized contracts) reached $627B (+99% YoY) at Q3 FY2026, of which ~$156B is recognizable within 12 months and ~$250B (40%) is the OpenAI commitment. RPO confirms Azure demand is contracted, not speculative — this raised the MSFT base-case probability from 45% to 60%.

---

## 8. TAX AND ESTATE PLANNING (Non-Resident Alien)

### 8.1 The NRA dividend and estate-tax problem
`tags: tax, estate, NRA, Taiwan, critical`
For a Taiwan-resident non-resident alien (NRA) holding US stocks: (1) Dividends are withheld at 30% (vs 15% for US residents). (2) Capital gains on US stocks are NOT taxed by the US for NRAs — actually better than US residents. (3) CRITICAL: US estate tax applies to US-situs assets above only a $60,000 exemption, at rates up to 40%. Taiwan has NO US estate-tax treaty. On a future ~$936k portfolio (~$800k US stocks), the estate-tax exposure could be ~$250k–$296k. This exposure already exists today because the portfolio exceeds $60,000.

### 8.2 Estate-tax mitigation structures
`tags: tax, estate, NRA, structures, solutions`
Four established legal structures to avoid US estate tax as an NRA: (1) Foreign blocker corporation — a non-US company holds the US stocks, so at death the heir inherits non-US-situs company shares (setup ~NT$30–50k; note tightened IRS anti-inversion rules require a specialist). (2) Ireland-domiciled UCITS ETFs (e.g., CSPX, VWCE via Interactive Brokers) instead of US-domiciled ETFs — Ireland's US treaty cuts dividend withholding to 15% AND the fund shares are not US-situs, eliminating estate-tax risk (cleanest solution). (3) Foreign non-grantor trust — more complex, best above $500k. (4) Term life insurance sized to cover the estate-tax bill (~$2–3k/year for $300k coverage) — pays the tax rather than avoiding it. Action: consult a Taiwan cross-border tax specialist (跨境稅務規劃) now; keep the W-8BEN current with the broker (it expires after 3 calendar years).

---

## 9. PORTFOLIO TRAJECTORY (no lump sums, current plan)

### 9.1 Base-case trajectory at 14.9%, $1,200/month from 2027
`tags: trajectory, projection, milestones`
Starting from $80,352 (May 2026), $1,000/month through Dec 2026 then $1,200/month: Dec 2026 ~$95,600; end-2031 ~$220,000; end-2036 ~$390,000; end-2041 ~$936,000 (~$3,120/month passive income at 4%). The $1.5M goal is reached ~2045 at $1,200/month, ~2042 at $1,500/month, ~2040 in the 18% AI-bull case. Contribution sensitivity at 2041: $1,000/mo → ~$753k; $1,200/mo → ~$909k; $1,500/mo → ~$1.14M.

### 9.2 The compounding inflection point
`tags: trajectory, compounding, milestone`
At $1,200/month, around 2029–2030 the portfolio's annual market growth (portfolio × 14.9%) first exceeds annual contributions ($14,400). From that point the money works harder than the contributions. By 2036 (~$390k+) the market adds ~$80–90k/year vs $14,400 contributed — roughly 6–7× leverage of effort. By 2041 the market adds ~10× annual contributions. The strategic implication: never interrupt contributions before this inflection.

### 9.3 Scenario outcomes at 2041
`tags: trajectory, scenarios, projection`
At $1,200/month from a $80,352 base: 18% AI-bull (~20% probability) → ~$1.9M, goal by ~2039; 14.9% base (~45%) → ~$936k–$1.36M depending on contribution, goal ~2044–2045; 12% conservative (~25%) → ~$786k–$922k, goal ~2049; 10.5% VOO-only (~10%) → ~$519k–$745k, goal ~2053+. Even the conservative 12% case produces meaningful wealth (~$2,600/month passive income). The worst realistic outcome is a delayed goal, not failure.

---

## 10. PENDING ACTIONS (as of June 2026)

### 10.1 Open action items
`tags: pending, actions, todo`
(1) URGENT: sell SGOV (~$3,057) and redeploy into MCO at ~77¢ — opportunity cost ~$6–7/week. (2) July 28 2026: Microsoft Q4 FY2026 earnings — apply the Azure trigger table to set August+ MSFT allocation (Azure ≥40% → $250/mo; 35–39% → $200; 30–34% → $150; <30% → $100; <25% two quarters → $0 and thesis review). (3) July 16 2026: TSMC Q2 2026 earnings — confirm the +50%+ net-income trajectory continues. (4) December 2026: AVGO Q4 earnings — reassess IV. (5) By 2028: convert TSMC ordinary shares (2330) to TSM ADR. (6) NOW: engage a cross-border tax specialist on NRA estate-tax structuring. (7) Sync updated canonical IVs (TSMC $620, AVGO $309) across all report files.

---

## 11. PRODUCT CONTEXT (ValueOS)

### 11.1 ValueOS product concept
`tags: product, ValueOS, business`
ValueOS is a planned MCP-based subscription product applying this exact Buffett owner-earnings framework for monthly retail investors targeting 12–15% growth toward passive income. Target audience: age 28–45, monthly income earners, anti-FOMO, long-term, AI-hype-skeptical. The six documented pain points: noise overload, FOMO paralysis, DCF complexity wall, advisor trust deficit, panic selling, and generic non-personalized advice. Proposed pricing: free tier as lead magnet, Core $19/month or $149/year, Deep $39/month. Differentiator/moat: pre-calculated canonical IVs updated each earnings, daily pushed buy-zone signals, personalized monthly allocation, panic-prevention scripts with the user's own numbers, the calibrated methodology itself, and the founder's TSMC semiconductor-industry edge (impossible to replicate positioning).

### 11.2 What users cannot get from free Claude
`tags: product, ValueOS, differentiation`
Six things the product provides that a fresh Claude session cannot: (1) pre-calculated canonical IVs already verified against SEC filings; (2) daily buy-zone signals pushed proactively (Claude only responds when asked); (3) monthly allocation personalized to the user's actual holdings and cost basis; (4) crash-response scripts with the user's specific numbers; (5) months of calibrated methodology (growth-capex add-back %, conservative growth haircuts, litigation normalization) baked in; (6) the founder's semiconductor-industry edge on TSMC. The unusual SaaS retention property: churn decreases as a user's portfolio grows, because the more they have invested via the framework, the more they need it maintained.

---

## 12. REPORTING SYSTEM

### 12.1 Daily market report format
`tags: reporting, format, system`
The recurring daily report is a styled HTML output containing: 52-week range bars, an IV column, a cents-per-$1 display, source badges distinguishing confirmed vs. estimated prices, and a canonical IV table for the five core stocks (MCO, V, TSM, MSFT, AVGO). The live DCF dashboard fetches prices, shows daily buy/hold/avoid signals, has a quarterly-update panel for entering SEC-filed actuals, and includes a full DCF breakdown table and term glossary. Output files use Chart.js with dark or paper-themed UI and slider-based scenario modeling.

### 12.2 Operating cadence
`tags: reporting, cadence, workflow`
Daily (~2 min): check the buy-zone signal and major news on holdings; no action unless a stock is in the buy zone or a business fundamental changed. Monthly (~30 min): deploy $300 VOO unconditionally, then allocate ~$700 by cents-per-$1; record the trade. Quarterly (~2 hrs): read each earnings 8-K/10-Q (actuals only), update the IV, answer the three thesis questions, check concentration. Yearly (one afternoon): compute actual return vs target, run the goal projection, write a one-paragraph thesis check per position, review tax timing, and confirm no single position exceeds 30%.

---

## END OF KNOWLEDGE BASE
