class Varghese_Ivan_Player extends Player {

    // Tuning these parameters based on the expected behaviors of the baseline bots
    private static final int WARMUP = 2; // Cooperate initially to build trust
    private static final double DEFECT_THRESHOLD = 0.60; // Forgive a little noise, but punish chronic defectors
    private static final int FORGIVE_INTERVAL = 15; // Break out of mutual defection spirals

    int selectAction(int n, int[] myHistory, int[] oppHistory1, int[] oppHistory2) {

        // Always start nice. This avoids triggering a retaliation spiral right out of the gate.
        if (n < WARMUP) {
            return 0; 
        }

        // Every 15 rounds, extend an olive branch. 
        // If we got stuck in a defection loop with a Tit-for-Tat player, this resets it.
        if (n % FORGIVE_INTERVAL == 0) {
            return 0; 
        }

        // Figure out how hostile both opponents have been over the whole match so far
        double defRate1 = defectionRate(oppHistory1, n);
        double defRate2 = defectionRate(oppHistory2, n);

        boolean opp1IsDefector = defRate1 > DEFECT_THRESHOLD;
        boolean opp2IsDefector = defRate2 > DEFECT_THRESHOLD;

        // Check if they actually bit us on the very last turn
        boolean opp1JustDefected  = (oppHistory1[n - 1] == 1);
        boolean opp2JustDefected  = (oppHistory2[n - 1] == 1);

        // If an opponent is generally a defector AND they just defected, strike back.
        // We only retaliate if they are actively being aggressive.
        if ((opp1IsDefector && opp1JustDefected) || (opp2IsDefector && opp2JustDefected)) {
            return 1; 
        }

        // Worst case scenario: being the only cooperator when everyone else defects yields 0 points.
        // If both opponents are chronic defectors, just cut our losses and defect.
        if (opp1IsDefector && opp2IsDefector) {
            return 1; 
        }

        // Default to cooperating
        return 0; 
    }

    // Helper to calculate the overall percentage of time an opponent has defected
    private double defectionRate(int[] history, int n) {
        if (n == 0) return 0.0;
        int defections = 0;
        for (int i = 0; i < n; i++) {
            if (history[i] == 1) {
                defections++;
            }
        }
        return (double) defections / n;
    }
}