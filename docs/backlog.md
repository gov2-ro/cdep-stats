# Backlog

Known issues and future improvements. Use `- [ ]` checkboxes; add enough context to act on later.

---

## PDF Parser — Known Limitations

- [ ] **`venituri_anuale_ron` double-counts income from co-owned properties**
  - ANI declarations require both spouses to list the same jointly-owned properties under sections 3.1 and 3.2 (cedarea folosinței). The parser sums all `amount RON/EUR` hits in section VII without deduplication, so rental income from shared plots appears twice. Venituri also include income for spouse, children, and other family members, plus one-off entries (real estate sales, dividends from family SRL) that inflate the annual figure. The field name `venituri_anuale_ron` is misleading — it is the total household sum, not the personal income of the titular.
  - Fix would require parsing by sub-section (1.1/1.2/1.3, 3.1/3.2, etc.) and choosing a clear semantic for the field (titular-only vs. household).
  - Audit case: Iordache Ion (leg-2024 idm=153) — stored 2,022,830 RON; titular-only ≈ 1,500,000 RON.

- [ ] **`suprafata_total_mp` ignores `cota-parte` (ownership share)**
  - The parser sums the full declared area for every imobil without applying the `Cota-parte` column. For properties co-owned by spouses at 1/2 share, the stored value is 2× the actual personal share. The cota-parte fraction also varies (1/3, 1/4, etc.).
  - Fix would require parsing the `Cota-parte` column per row and multiplying each area by the fraction before summing.
  - Audit case: Iordache Ion (leg-2024 idm=153) — all 73 terenuri + 10 cladiri are at 1/2; stored 10,858,310 m², actual personal share ≈ 5,429,155 m².


## Misc

- [ ] enhance avere.html with thumbnails for ppl and partide
- [ ] show cars, homes, teremnui as icons, one per each? - relative to suprafata or kph?
