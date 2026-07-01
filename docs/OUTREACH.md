# SeaVigil - outreach pack

Drafts to reach fisheries-enforcement NGOs, marine-conservation groups, Global Fishing Watch, and
National Geographic. Sender: Isma Abdelkader Di Carlo (independent / solo). Ask: **collaboration /
feedback** (low-friction), not a sale.
Links: live map https://seavigil.org · code https://github.com/iadicarlo/seavigil
Honest framing throughout: lead with what is genuinely ours, name the limits ourselves, keep every
claim scoped, stay non-commercial.

---

## One-pager (paste into an email or a PDF)

**SeaVigil - an open, explainable, near-real-time monitor for illegal fishing, with a reason, an authorization check, and an auditable dossier for every flag.**

SeaVigil watches priority waters for illegal-fishing behavior and, for every vessel it flags, answers
the three questions the cloud platforms leave open: *why* was it flagged, *is it authorized* to be
there, and *can the record be audited*. It runs offline on a laptop (no account, no cloud), and live
at **seavigil.org** on a single renewable-powered European VPS, in four languages. Open source,
non-commercial.

**What it does.**
- **Runs its own satellite detection.** Sentinel-1 SAR and Sentinel-2 optical vessel detection (the
  open Allen Institute / Skylight models) over the scenes and moments we choose, within hours of each
  satellite pass, and it saves a **true-color satellite photo of every detection**: a dark vessel
  stops being a dot and becomes a picture of the boat.
- **Detects live AIS behavior** from a continuous stream: apparent fishing (a calibrated,
  SHAP-explained classifier), going dark, at-sea encounters, and the AIS data-integrity leads working
  mariners say they trust (impossible movement / GNSS jamming, a moored vessel that is actually under
  way, one MMSI carrying more than one name), each with its most likely innocent explanation attached.
- **Grades jurisdiction and authorization.** Every flag is tagged with the EEZ it sits in and, where a
  vessel identity exists, checked against the RFMO authorizations on record, so a bare "foreign"
  becomes *authorized / authorization lapsed / no authorization on record / domestic*.
- **Packages each flag as an auditable dossier:** the reason, the place and time, the satellite photo,
  a SHA-256 integrity hash, and full data provenance, downloadable as JSON.

**What is genuinely ours (and what isn't).** Detection at planetary scale, multi-sensor fusion, and
near-real-time alerting are all now free and commoditized (Global Fishing Watch, Skylight), and even
the "inspection lead, not proof" honesty is shared. SeaVigil does not reinvent any of that. Its wedge
is the one intersection the cloud platforms do not occupy: **open-source, offline and air-gappable,
sovereign, and a per-flag auditable dossier** - the reason, the authorization grade against real RFMO
records, the satellite photo, and a tamper-evident evidence hash, for an authority that cannot (or
will not) depend on a foreign cloud login.

**Honest limits.** A flag is an *inspection lead, not courtroom proof* (encrypted VMS outranks public
AIS/SAR in fisheries law). "Fishing" is apparent, inferred from movement. AIS is blind to the ~75% of
industrial vessels that do not broadcast (the dark fleet) and is spoofable; SAR and optical see them
but carry no identity. National EEZ licences are not public, so an empty authorization record means
"no public record", not proof. It is a **targeting and evidence layer, not an enforcement one**: it
does not supply the patrol boat, the jurisdiction, or the owner behind a shell company, and it is
blind to crew and labor conditions and to small artisanal boats; its value is a better-targeted
inspection per patrol-day. Non-commercial (built on open GFW + WDPA data and open models).

**Proof points.** The fishing classifier is calibrated (**Brier 0.092** on ~408k held-out positions,
vessel-grouped split). Validated against the **CCAMLR IUU list**: of 18 listed vessels, GFW's registry
resolves 8 and SeaVigil grades all 8 as *unauthorized*. Live now at seavigil.org with the SAR and
optical detections, the satellite photos, the live AIS behaviors, and the dossiers. Code open at
github.com/iadicarlo/seavigil.

---

## Two-minute demo (what to walk them through)

1. **Open seavigil.org.** The map opens on the global monitor: flagged vessels worldwide, each a dot
   colored by behavior. The legend (top-left) names every type and is a live layer switch.
2. **Open `seavigil.org/?s2`** (the optical view, Galapagos) and click a **green** dot. The dossier
   opens with a **true-color satellite photo of the boat**, the reason it is flagged, the EEZ, the
   authorization status, and the integrity hash. *"This is not a blip, this is the boat."*
3. **Click an orange AIS dot.** The dossier shows the **SHAP attribution**: why this track scored as
   fishing (speed, turning, distance to shore). *"Every flag has a reason you can read."*
4. **Download the dossier (JSON).** It is the auditable evidence package, integrity hash and full
   provenance, that an officer or a journalist can verify independently.
5. **Open the About page** for the methodology, the calibration, and the cited sources (Science,
   Nature, NeurIPS), in four languages; or `?showcase` for the worldwide historical sample.

---

## Who to contact (shortlist)

Fisheries-enforcement NGOs that serve coastal states (best fit, would *use* it). Use **Email 2**.
- **Trygg Mat Tracking (TMT)** - technical partner to developing coastal/port/flag states, maintains
  the Combined IUU Vessel List. Contact via tm-tracking.org.
- **Stop Illegal Fishing** + the West Africa Task Force / FISH-i Africa - African IUU enforcement.
  Contact via stopillegalfishing.com.
- **Environmental Justice Foundation (EJF)** - IUU + West Africa + human rights at sea. Contact via
  ejfoundation.org (Oceans campaign).

Conservation / MPA NGOs (would champion or pilot). Use **Email 3**.
- **National Geographic Pristine Seas** - large-MPA establishment and defense (the Galapagos demo lands).
- **Marine Conservation Institute** - Marine Protection Atlas / Blue Parks, monitoring and enforcement.
- **Blue Ventures** - community marine conservation across the Global South, low-connectivity contexts.

Open-data / satellite peers (collaboration and feedback). Use **Email 1**.
- **SkyTruth** - satellite environmental monitoring, co-founded GFW. Contact via skytruth.org.
- **Global Fishing Watch** - you build on their data and the Skylight models.

For named contacts, a few minutes on each org's team page or LinkedIn beats a guessed address.
Start with **TMT** and **SkyTruth**: both are technical, mission-aligned, and used to evaluating
exactly this kind of tool.

---

## Email 1 - Global Fishing Watch / open-data peer (feedback / collaboration)

**Subject:** An explainable, offline triage layer built on your data and the Skylight models - your feedback?

Hi `[name]`,

I'm Isma Abdelkader Di Carlo, an independent developer. I built a small open, non-commercial tool,
SeaVigil, **on top of your work**: it trains on your open AIS labels, runs the open Allen
Institute / Skylight Sentinel-1 and Sentinel-2 vessel detectors over scenes I choose, and uses your
vessel-identity registry for authorization. I want to be upfront that I am not claiming to have
invented detection.

What it adds is the last mile the cloud platforms leave open: a **per-flag SHAP explanation** of why a
position scored as fishing, an **authorization grade** against the RFMO records, a **satellite photo of
each detection**, an **auditable per-incident dossier** (integrity hash + provenance), and a
**laptop-deployable, no-account, sovereign** footprint for low-capacity authorities.

I'd genuinely value your feedback: whether this is useful, whether I have framed your work fairly, and
whether there is a complementary direction worth pursuing. Live map and open code:
https://seavigil.org · https://github.com/iadicarlo/seavigil.

Thank you for making the data and the models open; none of this exists without it.

Isma Abdelkader Di Carlo

---

## Email 2 - Fisheries-enforcement NGO (collaboration / feedback)

**Subject:** Offline, explainable, authorization-graded fishing triage for low-capacity authorities - feedback?

Hi `[name]`,

I'm Isma Abdelkader Di Carlo, an independent developer. I've built SeaVigil, a free, non-commercial
tool that flags illegal-fishing behavior - apparent fishing, dark (non-broadcasting) vessels, going
dark, at-sea encounters - and produces a per-incident dossier with a plain, auditable reason for each
flag, an **authorization check against the RFMO records**, and a **satellite photo of the vessel**.

The deliberate difference from the cloud platforms: it runs **offline on a laptop, with no account**,
or live on a single sovereign, renewable-powered server, and it grades each foreign vessel against the
authorizations on record. It is meant for the place the well-resourced tools do not reach. Output is an
*inspection lead, not proof*, and I keep that explicit.

Given your work with coastal states, I'd really value your read: is the offline + explainable +
authorization angle useful to the partners you serve, and what would make it credible enough to pilot?
Live map + open code: https://seavigil.org · https://github.com/iadicarlo/seavigil.

Thanks for considering it,

Isma Abdelkader Di Carlo

---

## Email 3 - Conservation / MPA NGO / advocacy (feedback / story)

**Subject:** Making MPA enforcement auditable, offline, and visual - a Global-South angle, and your thoughts

Hi `[name]`,

I'm Isma Abdelkader Di Carlo, an independent developer. I built SeaVigil, a free, non-commercial tool
that turns vessel-movement and satellite signals into an **auditable, per-incident dossier** of
apparent fishing and dark vessels inside Marine Protected Areas and national waters, with a
**true-color satellite photo of each detection**, designed to run **offline on a laptop** so an
under-resourced authority can actually use it.

The story I think is worth telling is the **last mile**: making the *reason* a vessel was flagged
legible and defensible, putting a picture of the boat next to it, and doing it without a cloud budget.
I run my own Sentinel-1 and Sentinel-2 detection and have verified it inside reserves like the
Galapagos.

I'd value your perspective: whether this resonates with your conservation and enforcement work, and
whether there is a way it could support it. Live map + a short visual demo:
https://seavigil.org · https://github.com/iadicarlo/seavigil. Honest about the limits: it is an
inspection lead, not proof, and strictly non-commercial.

Warm regards,

Isma Abdelkader Di Carlo

---

## Before you send (gate)

1. Keep claims **scoped**: the SHAP attribution explains *the fishing detection itself*; the SAR /
   optical / behavior flags carry rule-based reasons, not SHAP. Do not imply proof of illegality.
2. Stay **non-commercial** and attribute Global Fishing Watch, the Allen Institute / Skylight, Marine
   Regions, and UNEP-WCMC / IUCN.
3. If anyone bites on a **pilot**, do a real-data demo first: their own AIS feed and a real boundary,
   out-of-sample.
4. Re-check the [README](../README.md) is current before linking it (the README and this pack drift as
   the product evolves; keep them in sync with seavigil.org).
