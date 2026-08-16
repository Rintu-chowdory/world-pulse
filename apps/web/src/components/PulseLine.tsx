export default function PulseLine() {
  return (
    <svg
      viewBox="0 0 1400 80"
      className="pulse-line w-full h-16"
      preserveAspectRatio="none"
    >
      <path
        d="M0,40 L120,40 L150,40 L170,10 L190,70 L210,20 L230,40 L340,40
           L400,40 L420,10 L440,70 L460,20 L480,40 L620,40
           L680,40 L700,10 L720,70 L740,20 L760,40 L900,40
           L960,40 L980,10 L1000,70 L1020,20 L1040,40 L1180,40
           L1240,40 L1260,10 L1280,70 L1300,20 L1320,40 L1400,40"
        fill="none"
        stroke="var(--live)"
        strokeWidth="2"
        strokeLinejoin="round"
        strokeLinecap="round"
      />
    </svg>
  );
}
