import {
  Cpu,
  MemoryStick,
  HardDrive,
  Monitor,
  Settings2,
  BatteryCharging,
  Camera,
  Wifi,
  ShieldCheck,
  Weight,
  Ruler,
  Smartphone,
  Palette,
  Zap,
} from "lucide-react";

interface Specification {
  name: string;
  value: string;
}

interface Props {
  specifications: Specification[];
}

/* ============================================================
   NORMALIZED SPECIFICATION
============================================================ */

interface NormalizedSpecification {
  name: string;
  value: string;
}

/* ============================================================
   NORMALIZE SPECIFICATION NAME
============================================================ */

function normalizeName(name: string): string {
  const value = name.toLowerCase().trim();

  if (
    value === "ram" ||
    value === "memory"
  ) {
    return "RAM";
  }

  if (
    value === "storage" ||
    value === "storage capacity" ||
    value.includes("rom") ||
    value.includes("internal storage") ||
    (value.includes("hard drive") && value.includes("size")) ||
    (value.includes("hard disk") && value.includes("size"))
  ) {
    return "Storage";
  }

  if (
    value === "processor" ||
    value === "cpu" ||
    value.includes("chipset")
  ) {
    return "Processor";
  }

  if (
    value === "graphics co processor" ||
    value === "video processor" ||
    value === "graphics coprocessor" ||
    value === "graphics processor" ||
    value === "gpu"
  ) {
    return "Graphics";
  }

  if (
    value === "graphics card description" ||
    value === "graphics description" ||
    value === "graphics chipset" ||
    value === "graphics chipset brand"
  ) {
    return "Graphics Type";
  }

  if (
    value === "graphics ram size" ||
    value === "graphics memory size" ||
    value === "video memory"
  ) {
    return "Graphics Memory";
  }

  if (
    value === "battery" ||
    value.includes("battery capacity") ||
    value.includes("battery energy content") ||
    (value.includes("battery") && value.includes("energy"))
  ) {
    return "Battery";
  }

  if (
    value === "battery cell type" ||
    value === "battery chemistry" ||
    value === "battery type"
  ) {
    return "Battery Type";
  }

  if (
    value === "charging" ||
    value.includes("charging")
  ) {
    return "Charging";
  }

  if (
    value === "refresh rate" ||
    value.includes("refresh")
  ) {
    return "Refresh Rate";
  }

  if (
    value === "screen protection" ||
    value.includes("glass")
  ) {
    return "Screen Protection";
  }

  if (
    value === "camera" ||
    value.includes("camera photo sensor")
  ) {
    return "Rear Camera";
  }

  if (
    value === "cellular" ||
    value.includes("network")
  ) {
    return "Network";
  }

  if (
    value === "water/dust resistance" ||
    value.includes("water resistance") ||
    value.includes("water/dust")
  ) {
    return "Water / Dust Resistance";
  }

  if (
    value.includes("weight")
  ) {
    return "Weight";
  }

  if (
    value.includes("dimension")
  ) {
    return "Dimensions";
  }

  if (
    value === "colour" ||
    value === "color"
  ) {
    return "Colour";
  }

  if (
    value === "operating system" ||
    value === "os"
  ) {
    return "Operating System";
  }

  if (
    value === "item type"
  ) {
    return "Type";
  }

  if (
    value === "form factor"
  ) {
    return "Form Factor";
  }

  if (
    value.includes("warranty")
  ) {
    return "Warranty";
  }

  return name;
}

/* ============================================================
   CREATE CLEAN SPECIFICATION LIST
============================================================ */

function normalizeSpecifications(
  specifications: Specification[]
): NormalizedSpecification[] {

  const values = new Map<string, string>();

  for (const spec of specifications || []) {

    if (!spec?.name || !spec?.value) {
      continue;
    }

    const originalName = spec.name
      .toLowerCase()
      .trim();

    const normalizedName = normalizeName(
      spec.name
    );

    /* --------------------------------------------------------
       IGNORE DUPLICATE / UNNECESSARY FIELDS
    --------------------------------------------------------- */

    if (
      originalName.includes(
        "screen size unit"
      )
    ) {
      continue;
    }

    /*
     * "Graphics Ram Type" (e.g. "VRAM") adds no
     * information beyond what "Graphics Memory"
     * already conveys — drop the duplicate.
     */
    if (
      originalName === "graphics ram type"
    ) {
      continue;
    }

    /*
     * We don't need the generic Amazon
     * "Water Resistant" field if IP rating exists.
     */
    if (
      originalName ===
        "water resistance level" &&
      specifications.some(
        (item) =>
          item.name
            ?.toLowerCase()
            .includes("water/dust resistance")
      )
    ) {
      continue;
    }

    /* --------------------------------------------------------
       DISPLAY
    --------------------------------------------------------- */

    /*
     * "Display" / "Display Technology" hold the panel
     * technology (e.g. "LED", "IPS") and can arrive in
     * either order. Merge whichever is seen into one
     * "Display" value instead of letting a later field
     * silently overwrite — or an earlier field silently
     * block — the other.
     *
     * "Screen Size" / "Display Size" hold the physical
     * size and are kept as their own field so they never
     * collide with, or shadow, the panel type.
     */

    if (
      originalName === "display" ||
      originalName === "display technology"
    ) {
      const existingDisplay = values.get("Display");

      values.set(
        "Display",
        existingDisplay
          ? `${existingDisplay} ${spec.value}`
          : spec.value
      );

      continue;
    }

    if (
      originalName === "display size" ||
      originalName === "screen size"
    ) {

      /*
       * Only use the first size value seen —
       * Display Size and Screen Size describe
       * the same thing.
       */
      if (!values.has("Screen Size")) {
        values.set(
          "Screen Size",
          spec.value
        );
      }

      continue;
    }

    /* --------------------------------------------------------
       CAMERA
    --------------------------------------------------------- */

    /*
     * Prefer the short "Camera" field.
     */

    if (
      originalName === "camera"
    ) {

      values.set(
        "Rear Camera",
        spec.value
      );

      continue;
    }

    if (
      originalName.includes(
        "rear facing camera photo sensor"
      )
    ) {

      if (!values.has("Rear Camera")) {

        values.set(
          "Rear Camera",
          spec.value
        );

      }

      continue;
    }

    /* --------------------------------------------------------
       WATER / DUST RESISTANCE
    --------------------------------------------------------- */

    if (
      originalName ===
        "water/dust resistance"
    ) {

      values.set(
        "Water / Dust Resistance",
        spec.value
      );

      continue;
    }

    /* --------------------------------------------------------
       NORMAL FIELD
    --------------------------------------------------------- */

    /*
     * Don't overwrite an already normalized value.
     */
    if (!values.has(normalizedName)) {

      values.set(
        normalizedName,
        spec.value
      );

    }
  }

  /* ----------------------------------------------------------
     CLEAN WARRANTY TEXT
  ----------------------------------------------------------- */

  if (values.has("Warranty")) {

    values.set(
      "Warranty",
      "1 Year Device Warranty • 6 Months Accessories"
    );

  }

  /* ----------------------------------------------------------
     PREFERRED DISPLAY ORDER
  ----------------------------------------------------------- */

  const preferredOrder = [
    "Operating System",
    "Processor",
    "RAM",
    "Storage",
    "Graphics",
    "Graphics Type",
    "Graphics Memory",
    "Display",
    "Screen Size",
    "Refresh Rate",
    "Battery",
    "Battery Type",
    "Charging",
    "Rear Camera",
    "Network",
    "Screen Protection",
    "Water / Dust Resistance",
    "Weight",
    "Dimensions",
    "Colour",
    "Form Factor",
    "Type",
    "Warranty",
  ];

  const result: NormalizedSpecification[] = [];

  /* ----------------------------------------------------------
     BUILD ORDERED RESULT
  ----------------------------------------------------------- */

  for (const name of preferredOrder) {

    const value = values.get(name);

    if (!value) {
      continue;
    }

    result.push({
      name,
      value,
    });

  }

  /* ----------------------------------------------------------
     UNKNOWN FIELDS
  ----------------------------------------------------------- */

  for (const [name, value] of values.entries()) {

    if (
      preferredOrder.includes(name)
    ) {
      continue;
    }

    result.push({
      name,
      value,
    });

  }

  return result;
}
/* ============================================================
   SPECIFICATION ICON
============================================================ */

function getSpecificationIcon(
  name: string
) {

  const value = name.toLowerCase();

  if (
    value.includes("processor")
  ) {
    return {
      Icon: Cpu,
      color: "text-blue-400",
      bg: "bg-blue-500/10",
    };
  }

  if (
    value.includes("graphics")
  ) {
    return {
      Icon: Cpu,
      color: "text-red-400",
      bg: "bg-red-500/10",
    };
  }

  if (
    value.includes("ram")
  ) {
    return {
      Icon: MemoryStick,
      color: "text-green-400",
      bg: "bg-green-500/10",
    };
  }

  if (
    value.includes("storage")
  ) {
    return {
      Icon: HardDrive,
      color: "text-yellow-400",
      bg: "bg-yellow-500/10",
    };
  }

  if (
    value.includes("display") ||
    value.includes("screen") ||
    value.includes("refresh")
  ) {
    return {
      Icon: Monitor,
      color: "text-purple-400",
      bg: "bg-purple-500/10",
    };
  }

  if (
    value.includes("battery")
  ) {
    return {
      Icon: BatteryCharging,
      color: "text-green-400",
      bg: "bg-green-500/10",
    };
  }

  if (
    value.includes("charging")
  ) {
    return {
      Icon: Zap,
      color: "text-yellow-400",
      bg: "bg-yellow-500/10",
    };
  }

  if (
    value.includes("camera")
  ) {
    return {
      Icon: Camera,
      color: "text-purple-400",
      bg: "bg-purple-500/10",
    };
  }

  if (
    value.includes("network")
  ) {
    return {
      Icon: Wifi,
      color: "text-blue-400",
      bg: "bg-blue-500/10",
    };
  }

  if (
    value.includes("protection") ||
    value.includes("water") ||
    value.includes("dust")
  ) {
    return {
      Icon: ShieldCheck,
      color: "text-green-400",
      bg: "bg-green-500/10",
    };
  }

  if (
    value.includes("weight")
  ) {
    return {
      Icon: Weight,
      color: "text-orange-400",
      bg: "bg-orange-500/10",
    };
  }

  if (
    value.includes("dimension")
  ) {
    return {
      Icon: Ruler,
      color: "text-blue-400",
      bg: "bg-blue-500/10",
    };
  }

  if (
    value.includes("colour") ||
    value.includes("color")
  ) {
    return {
      Icon: Palette,
      color: "text-pink-400",
      bg: "bg-pink-500/10",
    };
  }

  if (
    value.includes("operating system") ||
    value.includes("type") ||
    value.includes("form factor")
  ) {
    return {
      Icon: Smartphone,
      color: "text-blue-400",
      bg: "bg-blue-500/10",
    };
  }

  return {
    Icon: Settings2,
    color: "text-blue-400",
    bg: "bg-blue-500/10",
  };
}

/* ============================================================
   COMPONENT
============================================================ */

export default function SpecsCard({
  specifications,
}: Props) {

  const cleanSpecifications =
    normalizeSpecifications(
      specifications
    );

  return (
    <section className="rounded-3xl border border-slate-800 bg-slate-900/70 p-8 shadow-2xl backdrop-blur-xl">

      {/* ======================================================
          HEADER
      ======================================================= */}

      <div className="flex items-center gap-3">

        <Settings2
          size={22}
          className="text-blue-400"
        />

        <div>

          <p className="text-sm uppercase tracking-[0.2em] text-gray-500">
            Specifications
          </p>

          <h2 className="mt-2 text-3xl font-bold">
            Product Specifications
          </h2>

        </div>

      </div>

      {/* ======================================================
          SPECIFICATIONS
      ======================================================= */}

      {cleanSpecifications.length > 0 ? (

        <div className="mt-8 grid gap-5 sm:grid-cols-2">

          {cleanSpecifications.map(
            (spec, index) => {

              const {
                Icon,
                color,
                bg,
              } = getSpecificationIcon(
                spec.name
              );

              return (

                <div
                  key={`${spec.name}-${index}`}
                  className="group flex items-start gap-5 rounded-3xl border border-slate-700 bg-slate-800/60 p-6 transition-all duration-300 hover:-translate-y-1 hover:border-blue-500/30 hover:bg-slate-800"
                >

                  {/* Icon */}

                  <div
                    className={`flex h-14 w-14 shrink-0 items-center justify-center rounded-2xl ${bg}`}
                  >

                    <Icon
                      size={27}
                      className={color}
                    />

                  </div>

                  {/* Content */}

                  <div className="min-w-0 flex-1">

                    <p className="text-xs uppercase tracking-[0.18em] text-gray-500">
                      {spec.name}
                    </p>

                    <h3
                      className={`mt-2 break-words font-semibold leading-7 text-white ${
                        spec.name === "Warranty"
                          ? "text-base"
                          : "text-lg"
                      }`}
                    >
                      {spec.value}
                    </h3>

                  </div>

                </div>

              );
            }
          )}

        </div>

      ) : (

        /* ====================================================
           EMPTY STATE
        ===================================================== */

        <div className="mt-8 rounded-3xl border border-slate-700 bg-slate-800/60 p-8 text-center">

          <Settings2
            size={32}
            className="mx-auto text-gray-500"
          />

          <p className="mt-4 text-gray-400">
            No product specifications were found.
          </p>

        </div>

      )}

    </section>
  );
}