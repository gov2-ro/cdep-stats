GitHub Issue / PR text (ready to submit)

Title: fix: two PDF parser bugs — auto_count inflation (+4) and suprafata_mp truncation for large areas

Body:

Bug 1 — auto_count inflated by +4 per declaration
The vehicle regex uses \b word boundaries, so the subsection header 1. Autovehicule/autoturisme,
tractoare, maşini agricole, şalupe, iahturi... contributes 4 spurious matches. Every deputy's vehicle
count is overcounted by 4 regardless of how many vehicles they actually declared.
Fix: ^ anchor + re.MULTILINE — pdfplumber writes each table row starting at a new line; the header
never starts at ^.

Bug 2 — suprafata_total_mp truncated for areas ≥ 100,000 m²
RE_MP = re.compile(r"(\d{1,5}...)\s*m\s*²?") caps digit capture at 5. For a 6-digit area like 613134
m² the regex matches at offset +1, extracting 13134; for 7-digit areas like 1500000 m² it captures
00000 = 0, which is filtered by the > 5 guard, silently dropping the entire area.
Fix: change \d{1,5} to \d+.

Evidence (verified against PDFs):
| Deputy                       | Metric       | Stored       | Correct                  |
|------------------------------|--------------|--------------|--------------------------|
| Badea Nelu-Valentin (idm 15) | auto_count   | 14           | 10                       |
| Popa Alexandru (idm 249)     | suprafata_mp | 475,623 m²   | 1,375,623 m²             |
| Iordache Ion (idm 153)       | suprafata_mp | 1,897,569 m² | 12,197,569 m²            |
| Tuşa Adriana Diana (idm 309) | auto_count   | 4            | 0 (no vehicles declared) |

Both fixes applied to build_declaratii_avere.py and analiza_avere_pdf.py. Data regenerated from cached
PDFs. 