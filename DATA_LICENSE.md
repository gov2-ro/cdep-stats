# Licență date — cdep-stats

Preluat de la https://github.com/Endimion2k/cdep-api-poc/blob/main/DATA_LICENSE.md

## Sursa datelor

Toate datele sunt extrase din [www.cdep.ro](https://www.cdep.ro), site-ul oficial al **Camerei Deputaților** din România. Acestea sunt **informații de interes public** publicate de o autoritate publică în exercițiul mandatului parlamentar.

## Cadru legal

### Legea 544/2001 — Liberul acces la informațiile de interes public

Conform art. 2 lit. b) și art. 5 din [Legea 544/2001](https://legislatie.just.ro/Public/DetaliiDocument/31413), informațiile produse sau gestionate de autoritățile publice (inclusiv Camera Deputaților) sunt **din oficiu publice** și se comunică gratuit oricărei persoane fizice sau juridice care le solicită.

Datele despre activitatea parlamentară (deputați, voturi, proiecte legislative, interpelări, sancțiuni, moțiuni, comisii) intră fără echivoc în această categorie:
- Sunt produse în exercițiul mandatului public
- Sunt deja publicate pe cdep.ro
- Nu conțin informații personale clasificate

### GDPR și deputați ca persoane publice

Conform [Regulamentului UE 2016/679 (GDPR)](https://eur-lex.europa.eu/eli/reg/2016/679) art. 6 alin. (1) lit. e) și recital 47, prelucrarea datelor personale ale persoanelor publice (deputați) în exercițiul mandatului este permisă pe baza interesului public legitim al accesului la informații.

**Date pe care le colectăm despre deputați** (toate publice pe cdep.ro):
- Nume și prenume
- Partid politic, grup parlamentar
- Județul de circumscripție
- Data nașterii (când e publicată oficial)
- Componența comisiilor și delegațiilor
- Voturile nominale înregistrate
- Interpelările și moțiunile semnate
- Sancțiunile disciplinare aplicate

**Date pe care NU le colectăm** (informații personale neclasificate ca publice):
- CNP, serii de buletin, numere de pașaport
- Numere de telefon personale
- Adrese private
- Conturi bancare, declarații de avere detaliate (acestea există pe cdep.ro și ANI dar le exceptăm)
- Date despre familie / minori în custodie
- Orice informație medicală

### Drept de rectificare

Orice deputat sau persoană publică care identifică o eroare factuală în datele expuse poate solicita rectificarea prin deschiderea unui [issue pe GitHub](https://github.com/gov2-ro/cdep-stats/issues) cu template-ul „data correction". Rectificările vor fi propagate la următoarea rulare a workflow-ului zilnic.

## Licență

### Date

Datele expuse de acest API sunt republicate sub **[Open Government License v3.0](https://www.nationalarchives.gov.uk/doc/open-government-licence/version/3/)** (echivalent internațional al regimului „date publice de stat"). Permisă utilizarea liberă pentru:

- **Cercetare academică și jurnalistică**
- **Aplicații civic-tech** (dashboard-uri, vizualizări, boți)
- **Re-publicare** cu atribuire (link la cdep.ro și acest repo)
- **Utilizare comercială** (cu atribuire)

### Cod

Codul sursă (scrapere, schemas, builderi, pagini HTML, workflows) este disponibil sub aceeași licență **[Open Government License v3.0](https://www.nationalarchives.gov.uk/doc/open-government-licence/version/3/)** pentru consistență.

## Atribuire recomandată

Când utilizați aceste date într-un produs sau publicație, atribuirea recomandată este:

> Date din [www.cdep.ro](https://www.cdep.ro), agregate prin [cdep-api-poc](https://github.com/Endimion2k/cdep-api-poc)


---

*Acest document nu constituie consultanță juridică. Pentru interpretări precise ale Legii 544/2001 sau GDPR, consultați un specialist în drept.*
