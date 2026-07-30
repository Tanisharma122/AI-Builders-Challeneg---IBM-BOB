"use client";

interface Props {
  score: number; // 0–100
  size?: number; // SVG diameter in px, default 100
}

/**
 * SVG semi-circle (180°) arc gauge.
 * Colour ramp: <40 red · 40–70 amber · >70 green
 */
export function ScoreGauge({ score, size = 100 }: Props) {
  const clampedScore = Math.max(0, Math.min(100, score));

  // Arc geometry
  const cx = size / 2;
  const cy = size / 2;
  const r = size * 0.38;
  const strokeW = size * 0.1;

  // Semi-circle goes from left (180°) to right (0°) along the top
  const startAngle = Math.PI;           // left
  const endAngle   = 0;                 // right
  const fillAngle  = startAngle - (clampedScore / 100) * Math.PI;

  const toXY = (angle: number) => ({
    x: cx + r * Math.cos(angle),
    y: cy - r * Math.sin(angle),   // SVG y-axis is inverted
  });

  const start  = toXY(startAngle);
  const filled = toXY(fillAngle);
  const end    = toXY(endAngle);

  // Arc for track (full semi-circle)
  const trackD = `M ${start.x} ${start.y} A ${r} ${r} 0 0 1 ${end.x} ${end.y}`;

  // Arc for filled portion
  const largeArc = clampedScore > 50 ? 1 : 0;
  const fillD = clampedScore > 0
    ? `M ${start.x} ${start.y} A ${r} ${r} 0 ${largeArc} 1 ${filled.x} ${filled.y}`
    : "";

  // Colour
  const colour =
    clampedScore > 70 ? "#22c55e" :
    clampedScore > 40 ? "#f59e0b" :
                        "#ef4444";

  return (
    <div className="flex flex-col items-center" style={{ width: size }}>
      <svg width={size} height={size * 0.6} viewBox={`0 0 ${size} ${size * 0.6}`}>
        {/* Track */}
        <path
          d={trackD}
          fill="none"
          stroke="#e5e7eb"
          strokeWidth={strokeW}
          strokeLinecap="round"
        />
        {/* Filled arc */}
        {fillD && (
          <path
            d={fillD}
            fill="none"
            stroke={colour}
            strokeWidth={strokeW}
            strokeLinecap="round"
          />
        )}
        {/* Score label */}
        <text
          x={cx}
          y={cy * 0.95}
          textAnchor="middle"
          fontSize={size * 0.22}
          fontWeight="bold"
          fill={colour}
        >
          {clampedScore}
        </text>
        <text
          x={cx}
          y={cy * 1.2}
          textAnchor="middle"
          fontSize={size * 0.1}
          fill="#9ca3af"
        >
          / 100
        </text>
      </svg>
    </div>
  );
}
