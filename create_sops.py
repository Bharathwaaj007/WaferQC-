import os
import yaml

SOP_DIR = r"C:\Users\LENOVO\.gemini\antigravity\scratch\wafer_sem\data\sop_knowledge_base"
os.makedirs(SOP_DIR, exist_ok=True)

sops = [
    {
        "sop_id": "SOP-LIT-01",
        "title": "Lithography Focus Drift",
        "process_area": "Lithography",
        "related_defect_classes": ["bridge"],
        "disclaimer": "ILLUSTRATIVE HYPOTHESIS — not a validated fab procedure",
        "root_causes": [
            "Wafer chuck z-stage positioning deviation or thermal drift during stepper exposure.",
            "Laser leveling sensor optical misalignment due to backside wafer contamination."
        ],
        "checks": [
            "Verify chuck flatness interferometer telemetry and auto-focus offset log on stepper unit.",
            "Perform Focus-Exposure Matrix (FEM) test wafer review to inspect Bossung curves."
        ],
        "corrective_actions": [
            "Recalibrate auto-focus optical sensors and execute chuck plane leveling compensation.",
            "Quarantine current litho lot for critical dimension (CD) SEM review."
        ]
    },
    {
        "sop_id": "SOP-LIT-02",
        "title": "Lithography Dose Drop / Underexposure",
        "process_area": "Lithography",
        "related_defect_classes": ["bridge"],
        "disclaimer": "ILLUSTRATIVE HYPOTHESIS — not a validated fab procedure",
        "root_causes": [
            "Excimer laser energy pulse degradation or attenuator calibration offset.",
            "Illumination optic fogging or photoresist outgassing deposits on final lens element."
        ],
        "checks": [
            "Review pulse energy sensor trend logs across previous 50 exposure runs.",
            "Measure resist line-space space CD using automated CD-SEM."
        ],
        "corrective_actions": [
            "Perform laser chamber gas refill and energy calibration routine.",
            "Schedule scanner optic inspection and nitrogen purge line purge verification."
        ]
    },
    {
        "sop_id": "SOP-LIT-03",
        "title": "Photoresist Scumming and Footing",
        "process_area": "Lithography",
        "related_defect_classes": ["bridge", "particle"],
        "disclaimer": "ILLUSTRATIVE HYPOTHESIS — not a validated fab procedure",
        "root_causes": [
            "Incomplete photoresist dissolution in developer bath or developer nozzle pressure drop.",
            "Post-exposure bake (PEB) hotplate temperature non-uniformity causing residual unexposed polymer."
        ],
        "checks": [
            "Inspect developer puddle dispense uniformity and nozzle pressure gauge readings.",
            "Check 9-point thermal calibration data for PEB track bake stations."
        ],
        "corrective_actions": [
            "Purge and replace developer dispense filter and verify nozzle spray profile.",
            "Recalibrate multi-zone PID controllers on PEB hotplate module."
        ]
    },
    {
        "sop_id": "SOP-LIT-04",
        "title": "Stepper Overlay Shift",
        "process_area": "Lithography",
        "related_defect_classes": ["bridge"],
        "disclaimer": "ILLUSTRATIVE HYPOTHESIS — not a validated fab procedure",
        "root_causes": [
            "Inter-die alignment mark damage from previous chemical-mechanical planarization.",
            "Thermal expansion mismatch between reticle stage and wafer chuck stage."
        ],
        "checks": [
            "Analyze 5-point overlay error vector map across wafer perimeter.",
            "Verify reticle magnification and rotation correction coefficients."
        ],
        "corrective_actions": [
            "Apply feed-forward alignment compensation matrix for downstream wafers.",
            "Inspect reticle alignment marks and clean fiducial optics."
        ]
    },
    {
        "sop_id": "SOP-ETC-01",
        "title": "Plasma Etch Polymer Residue",
        "process_area": "Etch",
        "related_defect_classes": ["bridge", "particle"],
        "disclaimer": "ILLUSTRATIVE HYPOTHESIS — not a validated fab procedure",
        "root_causes": [
            "Excessive passivation chemistry (CF4/CHF3 ratio skew) during trench etch.",
            "Insufficient post-etch ash/strip process oxygen radical density."
        ],
        "checks": [
            "Measure optical emission spectroscopy (OES) endpoint fluorocarbon ratio trace.",
            "Inspect wafer edge bevel under optical review for polymer ring accumulation."
        ],
        "corrective_actions": [
            "Adjust passivation gas mass flow controller (MFC) setpoint and verify flow calibration.",
            "Execute downstream dry strip chamber oxygen plasma clean cycle."
        ]
    },
    {
        "sop_id": "SOP-ETC-02",
        "title": "Bias RF Power Low / Incomplete Trench Clearing",
        "process_area": "Etch",
        "related_defect_classes": ["bridge"],
        "disclaimer": "ILLUSTRATIVE HYPOTHESIS — not a validated fab procedure",
        "root_causes": [
            "Bias RF match network capacitor tuning stall preventing efficient ion bombardment.",
            "Degraded electrostatic chuck (ESC) RF coupling connection."
        ],
        "checks": [
            "Inspect forward vs reflected RF power log during trench clear step.",
            "Measure trench depth profile using cross-sectional focus ion beam (FIB-SEM)."
        ],
        "corrective_actions": [
            "Perform RF impedance matching network calibration and capacitor motor test.",
            "Inspect ESC surface contact pins for arcing or resistive oxidation."
        ]
    },
    {
        "sop_id": "SOP-ETC-03",
        "title": "Etch Chamber Wall Flaking Contamination",
        "process_area": "Etch",
        "related_defect_classes": ["particle"],
        "disclaimer": "ILLUSTRATIVE HYPOTHESIS — not a validated fab procedure",
        "root_causes": [
            "Al2O3 / Y2O3 chamber liner coating delamination after extended RF hours.",
            "Stress peeling of accumulated polymer from anodized chamber upper lid."
        ],
        "checks": [
            "Check chamber total RF hours counter against preventive maintenance threshold.",
            "Perform dark-field wafer surface inspection on blank monitor wafer."
        ],
        "corrective_actions": [
            "Initiate chamber wet clean and replace ceramic shield kit.",
            "Execute seasoning run with 25 dummy wafers before releasing chamber to production."
        ]
    },
    {
        "sop_id": "SOP-CMP-01",
        "title": "CMP Slurry Particle Agglomeration",
        "process_area": "CMP",
        "related_defect_classes": ["particle", "scratch"],
        "disclaimer": "ILLUSTRATIVE HYPOTHESIS — not a validated fab procedure",
        "root_causes": [
            "Slurry delivery loop point-of-use (POU) filter rupture or pressure differential spike.",
            "Slurry pH destabilization causing secondary particle clustering above 0.5 microns."
        ],
        "checks": [
            "Inspect POU depth filter delta-P sensor logs and flow rate monitors.",
            "Test slurry zeta potential and particle size distribution via dynamic light scattering."
        ],
        "corrective_actions": [
            "Flush slurry delivery line with DI water and replace 0.2 um POU cartridge.",
            "Verify slurry barrel expiration date and agitation recirculation rate."
        ]
    },
    {
        "sop_id": "SOP-CMP-02",
        "title": "CMP Polishing Pad Wear and Glazing",
        "process_area": "CMP",
        "related_defect_classes": ["scratch"],
        "disclaimer": "ILLUSTRATIVE HYPOTHESIS — not a validated fab procedure",
        "root_causes": [
            "Pad groove depth worn below critical threshold preventing debris fluid transport.",
            "Polyurethane pore glazing due to inadequate in-situ diamond conditioning."
        ],
        "checks": [
            "Measure residual pad groove depth using optical laser triangulation sensor.",
            "Inspect pad surface texture for glazed slick spots."
        ],
        "corrective_actions": [
            "Execute aggressive pad conditioning recovery cycle.",
            "Replace CMP polishing pad and recalibrate platen baseline height."
        ]
    },
    {
        "sop_id": "SOP-CMP-03",
        "title": "Diamond Conditioning Disc Wear and Fracture",
        "process_area": "CMP",
        "related_defect_classes": ["scratch", "particle"],
        "disclaimer": "ILLUSTRATIVE HYPOTHESIS — not a validated fab procedure",
        "root_causes": [
            "Diamond grit detachment from conditioning disc substrate migrating into slurry pad interface.",
            "Excessive conditioning downforce causing diamond chipping and micro-scratching."
        ],
        "checks": [
            "Microscopic visual inspection of diamond conditioner disc for missing grits.",
            "Correlate scratch track orientation with conditioning arm sweep oscillation path."
        ],
        "corrective_actions": [
            "Immediately take CMP platen offline and replace diamond conditioning head.",
            "Discard currently mounted pad and perform full platen deck DIW washdown."
        ]
    },
    {
        "sop_id": "SOP-DEP-01",
        "title": "CVD/ALD Showerhead Flaking Contamination",
        "process_area": "Deposition",
        "related_defect_classes": ["particle"],
        "disclaimer": "ILLUSTRATIVE HYPOTHESIS — not a validated fab procedure",
        "root_causes": [
            "Thermal expansion stress causing deposited film spalling from gas distribution plate.",
            "Improper in-situ NF3 plasma clean recipe leaving friable byproduct residue."
        ],
        "checks": [
            "Inspect particle map spatial distribution for radial pattern centered on gas inlets.",
            "Review in-situ chamber clean duration and mass spectrometer effluent traces."
        ],
        "corrective_actions": [
            "Execute deep chamber NF3 clean recipe and extend purge cycle duration.",
            "Inspect showerhead assembly via vacuum viewport for blistering or discoloration."
        ]
    },
    {
        "sop_id": "SOP-DEP-02",
        "title": "PVD Target Micro-Arcing and Splatter",
        "process_area": "Deposition",
        "related_defect_classes": ["particle"],
        "disclaimer": "ILLUSTRATIVE HYPOTHESIS — not a validated fab procedure",
        "root_causes": [
            "Dielectric breakdown at sputter target edge redeposition zone producing micro-arcs.",
            "Target nodule formation ejecting macroscopic metal droplets toward wafer."
        ],
        "checks": [
            "Check DC power supply arc suppression circuit event counter logs.",
            "Inspect target erosion racetrack visually through load lock camera."
        ],
        "corrective_actions": [
            "Run target burn-in seasoning paste-down at reduced power.",
            "If arc counts exceed 50/hour, replace sputter cathode target."
        ]
    },
    {
        "sop_id": "SOP-CLN-01",
        "title": "Wet Clean Particle Excursion",
        "process_area": "Wet Clean",
        "related_defect_classes": ["particle"],
        "disclaimer": "ILLUSTRATIVE HYPOTHESIS — not a validated fab procedure",
        "root_causes": [
            "Megasonic transducer cavitation degradation or delamination from tank bottom.",
            "Recirculation bath particle filter breakthrough in SC-1 (NH4OH/H2O2/H2O) bath."
        ],
        "checks": [
            "Measure megasonic acoustic power density using hydrophone sensor probe.",
            "Inspect liquid particle counter (LPC) trend for SC-1 bath line."
        ],
        "corrective_actions": [
            "Drain, clean, and recharge SC-1 chemical bath with fresh chemistry.",
            "Replace 0.05 um chemical filter elements in recirculation loop."
        ]
    },
    {
        "sop_id": "SOP-CLN-02",
        "title": "Single-Wafer Spin Clean Rinse Nozzle Misalignment",
        "process_area": "Wet Clean",
        "related_defect_classes": ["particle", "scratch"],
        "disclaimer": "ILLUSTRATIVE HYPOTHESIS — not a validated fab procedure",
        "root_causes": [
            "DI water high-pressure spray nozzle arm home position stepper error.",
            "Partial droplet crystallization on nozzle tip causing spray deflection or stream breakup."
        ],
        "checks": [
            "Verify nozzle arm sweep trajectory using optical strobe alignment jig.",
            "Examine dry water-mark pattern across wafer center and edge."
        ],
        "corrective_actions": [
            "Clean rinse nozzle assembly with ultrasonic IPA bath.",
            "Recalibrate sweep angle servo motor zero position."
        ]
    },
    {
        "sop_id": "SOP-HND-01",
        "title": "Wafer Handling Robot End-Effector Abrasion",
        "process_area": "Handling",
        "related_defect_classes": ["scratch", "particle"],
        "disclaimer": "ILLUSTRATIVE HYPOTHESIS — not a validated fab procedure",
        "root_causes": [
            "Vacuum wand or end-effector ceramic contact pin wear creating particulate debris.",
            "Cassette slot optical mapper offset causing wafer scraping during load/unload."
        ],
        "checks": [
            "Inspect FOUP cassette entry slot clearance and robot teach points.",
            "Examine wafer backside and bevel edge for collinear scratch signatures."
        ],
        "corrective_actions": [
            "Re-teach transfer robot pick/place coordinates with teaching jig.",
            "Replace elastomer vacuum pads and ceramic positioning pins on robot blade."
        ]
    }
]

for sop in sops:
    filepath = os.path.join(SOP_DIR, f"{sop['sop_id']}.yaml")
    with open(filepath, "w", encoding="utf-8") as f:
        yaml.dump(sop, f, sort_keys=False, default_flow_style=False, allow_unicode=True)
    print(f"Created: {sop['sop_id']}.yaml")

print(f"Total SOPs generated: {len(sops)}")
