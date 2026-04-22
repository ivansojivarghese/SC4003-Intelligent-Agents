/**
 * Adaptive Graduated Response Player
 *
 * Strategy overview:
 * ─────────────────────────────────────────────────────────────────────────────
 * This player uses a *per-opponent* reputation model combined with graduated,
 * forgiving retaliation.  The core ideas are:
 *
 *  1. REPUTATION TRACKING  – maintain a rolling "defection rate" for each
 *     opponent independently.  A full-history window is used so the estimate
 *     gets sharper as the match progresses.
 *
 *  2. GRADUATED THRESHOLD  – cooperate unless the opponent's defection rate
 *     exceeds a threshold (DEFECT_THRESHOLD = 0.6).  This is lenient enough
 *     to tolerate a few early defections (e.g. FreakyPlayer that turned nasty)
 *     while still retaliating firmly against persistent defectors.
 *
 *  3. OPPONENT-AWARE DECISION  – we look at BOTH opponents together.  If
 *     either opponent is classified as a defector AND at least one of them has
 *     defected in the very last round, we defect.  Against two cooperative
 *     opponents we always cooperate (maximises mutual payoff).
 *
 *  4. OCCASIONAL FORGIVENESS  – every FORGIVE_INTERVAL rounds we cooperate
 *     regardless, giving a defector a chance to switch back to cooperation.
 *     This helps escape mutual-defection traps and recovers value against
 *     T4TPlayer / TolerantPlayer that may have been mis-triggered.
 *
 *  5. WARM START  – cooperate for the first WARMUP rounds to establish trust
 *     and gather meaningful history before judging.
 *
 * Performance reasoning (against the six baseline players):
 *  • NicePlayer        – both sides cooperate → high mutual payoff (6 pts/round)
 *  • NastyPlayer       – we defect back quickly; mutual defect (5 pts) > being
 *                        exploited (0 pts)
 *  • RandomPlayer      – ~50% defect rate → below threshold → we cooperate more
 *                        than we defect, slightly above average outcome
 *  • TolerantPlayer    – cooperates unless majority defect; we cooperate →
 *                        both stay cooperative
 *  • FreakyPlayer(C)   – always cooperates → mutual cooperation
 *  • FreakyPlayer(D)   – always defects → we retaliate after WARMUP
 *  • T4TPlayer         – mirrors us; we cooperate → it cooperates back
 * ─────────────────────────────────────────────────────────────────────────────
 */
class lastname_firstname_Player extends Player {

    // ── tuneable constants ──────────────────────────────────────────────────

    /** Number of opening rounds in which we always cooperate. */
    private static final int WARMUP = 2;

    /**
     * If an opponent's cumulative defection rate exceeds this value we
     * consider them a defector.  0.6 means "more than 60 % of their moves
     * were defections".
     */
    private static final double DEFECT_THRESHOLD = 0.60;

    /**
     * Every FORGIVE_INTERVAL rounds we cooperate unconditionally to give
     * defectors a chance to reform (also smooths out noise from RandomPlayer).
     */
    private static final int FORGIVE_INTERVAL = 15;

    // ── main logic ──────────────────────────────────────────────────────────

    int selectAction(int n,
                     int[] myHistory,
                     int[] oppHistory1,
                     int[] oppHistory2) {

        // ── 1. Warm-start: cooperate for the first few rounds ──────────────
        if (n < WARMUP) {
            return 0; // cooperate
        }

        // ── 2. Periodic forgiveness ────────────────────────────────────────
        if (n % FORGIVE_INTERVAL == 0) {
            return 0; // cooperate
        }

        // ── 3. Compute defection rates ─────────────────────────────────────
        double defRate1 = defectionRate(oppHistory1, n);
        double defRate2 = defectionRate(oppHistory2, n);

        boolean opp1IsDefector = defRate1 > DEFECT_THRESHOLD;
        boolean opp2IsDefector = defRate2 > DEFECT_THRESHOLD;

        // ── 4. Decision rule ───────────────────────────────────────────────
        //
        // Defect only when:
        //   (a) at least one opponent is classified as a defector, AND
        //   (b) that opponent actually defected last round
        //       (immediate reactive element, prevents over-punishing noise).
        //
        // This is a "tit-for-tat with tolerance" extended to two opponents.

        boolean opp1JustDefected  = (oppHistory1[n - 1] == 1);
        boolean opp2JustDefected  = (oppHistory2[n - 1] == 1);

        if ((opp1IsDefector && opp1JustDefected)
                || (opp2IsDefector && opp2JustDefected)) {
            return 1; // defect
        }

        // ── 5. Extra safety: if BOTH opponents are chronic defectors,
        //    always defect (avoids being the only cooperator = worst payoff).
        if (opp1IsDefector && opp2IsDefector) {
            return 1; // defect
        }

        return 0; // cooperate
    }

    // ── helper ──────────────────────────────────────────────────────────────

    /**
     * Returns the fraction of rounds [0, n) in which the given opponent
     * defected.  Returns 0 if n == 0 (no history yet).
     */
    private double defectionRate(int[] history, int n) {
        if (n == 0) return 0.0;
        int defections = 0;
        for (int i = 0; i < n; i++) {
            if (history[i] == 1) defections++;
        }
        return (double) defections / n;
    }
}
