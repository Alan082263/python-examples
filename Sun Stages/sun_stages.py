"""
sun_stages.py

Interactive version: you choose a star's name and mass, and the
program walks through what actually happens to a star of that size,
one stage at a time.

Stars below ~8 solar masses end as white dwarfs.
Stars at or above ~8 solar masses go supernova, leaving behind
either a neutron star or a black hole.
"""

SUPERNOVA_THRESHOLD = 8.0  # solar masses
BLACK_HOLE_THRESHOLD = 25.0  # solar masses
SOLAR_LIFETIME_YEARS = 10e9  # the Sun's approximate main-sequence lifetime


def press_enter(prompt="Press Enter to continue..."):
    input(prompt)


def estimate_lifetime_years(mass_in_solar_masses):
    """
    Rough mass-luminosity-based estimate of a star's main-sequence
    lifetime: more massive stars burn fuel far faster, so lifetime
    scales roughly as mass^-2.5. This is an approximation astronomers
    use for back-of-the-envelope estimates, not an exact figure.
    """
    return SOLAR_LIFETIME_YEARS * (mass_in_solar_masses ** -2.5)


def format_years(years):
    """Turn a raw year count into a friendlier, rounded description."""
    if years >= 1e9:
        return f"~{years / 1e9:.1f} billion years"
    elif years >= 1e6:
        return f"~{years / 1e6:.1f} million years"
    elif years >= 1e3:
        return f"~{years / 1e3:.1f} thousand years"
    else:
        return f"~{years:.0f} years"


def get_star_input():
    name = input("Name your star: ").strip() or "Star"
    while True:
        raw = input(f"Enter {name}'s mass in solar masses (e.g. 1 = Sun-like, 20 = massive): ").strip()
        try:
            mass = float(raw)
            if mass <= 0:
                print("Mass has to be greater than zero.")
                continue
            return name, mass
        except ValueError:
            print("That's not a number — try something like 1, 8, or 20.")


class Sun:
    """
    Any star, regardless of final mass, starts here: fusing hydrogen
    into helium in its core, held in balance between gravity pulling
    inward and fusion pushing outward.
    """

    def __init__(self, mass_in_solar_masses=1.0, name="Sun"):
        self.name = name
        self.mass = mass_in_solar_masses
        self.stage = "Main Sequence"
        self.core_element = "Hydrogen"

    def describe(self):
        print(f"\n--- {self.name} ---")
        print(f"Mass: {self.mass} solar masses")
        print(f"Stage: {self.stage}")
        print(f"Core fusing: {self.core_element}")

    def fuse_hydrogen(self):
        """Stage 1: Main sequence."""
        self.stage = "Main Sequence"
        self.core_element = "Hydrogen"
        print(
            f"{self.name} spends most of its life here, fusing hydrogen into "
            "helium, held in balance between gravity pulling in and fusion "
            "pushing out."
        )

    def become_white_dwarf(self):
        """
        Stage 2 (low-mass path): once the core runs out of hydrogen,
        a star like this sheds its outer layers and the core cools
        into a white dwarf — no supernova required.
        """
        self.stage = "White Dwarf"
        self.core_element = "Carbon/Oxygen (inert)"
        print(
            f"{self.name} isn't massive enough to fuse past carbon and oxygen. "
            "It puffs off its outer layers as a glowing shell of gas, leaving "
            "behind a slowly cooling white dwarf — no explosion needed."
        )


class MassiveStar(Sun):
    """
    A star massive enough to fuse all the way to iron and end in a
    supernova. Inherits the basic setup from Sun.
    """

    FUSION_LADDER = ["Hydrogen", "Helium", "Carbon", "Neon", "Oxygen", "Silicon", "Iron"]

    def __init__(self, mass_in_solar_masses=20.0, name="Massive Star"):
        super().__init__(mass_in_solar_masses, name)
        self._ladder_index = 0

    # Each entry explains, for the *resulting* element: what triggers this
    # stage, and what the fusion reaction itself does.
    FUSION_INFO = {
        "Helium": {
            "trigger": "Once the core runs low on hydrogen, fusion can't hold gravity "
                       "back anymore. The core contracts, and that contraction heats it "
                       "up until it's hot enough to fuse the next element.",
            "reaction": "Three helium nuclei slam together to form one carbon nucleus "
                        "(the 'triple-alpha process'), releasing energy and pausing the "
                        "collapse again — temporarily.",
        },
        "Carbon": {
            "trigger": "Helium runs out, so the core contracts and heats up further.",
            "reaction": "Carbon nuclei fuse to form heavier products like neon and "
                        "magnesium, releasing energy but noticeably less per reaction "
                        "than the stages before it.",
        },
        "Neon": {
            "trigger": "Carbon is spent; the core contracts and heats up again.",
            "reaction": "Neon nuclei absorb and re-emit particles to build up "
                        "oxygen and magnesium — a stage that burns through its fuel "
                        "far faster than carbon did.",
        },
        "Oxygen": {
            "trigger": "Neon is exhausted, so the core contracts and heats up once more.",
            "reaction": "Oxygen nuclei fuse into silicon and sulfur, releasing energy "
                        "over a timescale now measured in months rather than millennia.",
        },
        "Silicon": {
            "trigger": "Oxygen is used up; the core contracts and heats up sharply.",
            "reaction": "Silicon nuclei fuse and rearrange into iron and nickel — this "
                        "stage burns itself out in roughly a day.",
        },
        "Iron": {
            "trigger": "Silicon is exhausted, leaving a core that's almost pure iron.",
            "reaction": "Iron has the most tightly bound nucleus of any element, so "
                        "fusing it further doesn't release energy — it costs energy. "
                        "Fusion effectively stops here, no matter how hot the core gets.",
        },
    }

    def burn_next_element(self):
        """Stage 2: Advanced fusion, element by element up to iron."""
        if self._ladder_index >= len(self.FUSION_LADDER) - 1:
            print(f"{self.name} has nothing left to fuse — the core is now iron.")
            return
        self._ladder_index += 1
        self.core_element = self.FUSION_LADDER[self._ladder_index]
        self.stage = f"Fusing {self.core_element}"
        info = self.FUSION_INFO[self.core_element]
        print(f"\n{self.name} now fuses {self.core_element} in its core.")
        print(f"Why now: {info['trigger']}")
        print(f"What happens: {info['reaction']}")

    def iron_core_collapse(self):
        """Stage 3: Core collapse."""
        self.stage = "Core Collapse"
        print(
            f"\n{self.name}'s iron core can no longer generate outward pressure "
            "through fusion — iron doesn't release energy when fused, it absorbs "
            "it. With nothing left pushing back, gravity wins instantly. In under "
            "a second, the core collapses from roughly the size of Earth down to "
            "about 20 km across, and protons and electrons are crushed together "
            "into neutrons."
        )

    def supernova(self):
        """Stage 4: The explosion itself."""
        self.stage = "Supernova"
        print(
            f"{self.name} detonates! A shockwave rips through the outer "
            "layers, briefly outshining an entire galaxy, and scattering "
            "heavy elements into space."
        )

    def remnant(self):
        """Stage 5: Neutron star or black hole, depending on mass."""
        if self.mass < BLACK_HOLE_THRESHOLD:
            self.stage = "Neutron Star"
            print(
                f"What remains of {self.name} is a neutron star — roughly "
                "the size of a city, but packing more mass than the Sun."
            )
        else:
            self.stage = "Black Hole"
            print(
                f"{self.name} was massive enough that its core keeps "
                "collapsing past the neutron star stage, into a black hole."
            )


def run_low_mass_path(name, mass):
    star = Sun(mass_in_solar_masses=mass, name=name)
    star.describe()
    press_enter()

    star.fuse_hydrogen()
    press_enter()

    star.become_white_dwarf()
    star.describe()


def run_supernova_path(name, mass):
    star = MassiveStar(mass_in_solar_masses=mass, name=name)
    star.describe()
    press_enter()

    star.fuse_hydrogen()
    press_enter()

    for _ in range(len(MassiveStar.FUSION_LADDER) - 1):
        star.burn_next_element()
        press_enter()

    star.iron_core_collapse()
    press_enter()

    star.supernova()
    press_enter()

    star.remnant()
    star.describe()


def run_life_cycle():
    print("=== Build Your Own Star ===")
    name, mass = get_star_input()

    print(f"\nSimulating {name} at {mass} solar masses...")

    lifetime = estimate_lifetime_years(mass)
    outcome = "go supernova" if mass >= SUPERNOVA_THRESHOLD else "become a white dwarf"
    print(f"At this mass, {name} will spend {format_years(lifetime)} on the main "
          f"sequence before it starts the process to {outcome}.")
    press_enter()

    if mass < SUPERNOVA_THRESHOLD:
        run_low_mass_path(name, mass)
    else:
        run_supernova_path(name, mass)

    print("\n=== Simulation complete ===")


if __name__ == "__main__":
    run_life_cycle()
