class lastname_firstname_Player extends Player {
    
    // Helper method to calculate the recent defection rate of a specific opponent
    private double getRecentDefectionRate(int n, int[] history, int windowSize) {
        if (n == 0) return 0.0;
        
        int start = Math.max(0, n - windowSize);
        int defects = 0;
        int totalConsidered = n - start;
        
        for (int i = start; i < n; i++) {
            if (history[i] == 1) { // 1 represents defection
                defects++;
            }
        }
        return (double) defects / totalConsidered;
    }

    // Main action selection logic
    int selectAction(int n, int[] myHistory, int[] oppHistory1, int[] oppHistory2) {
        // Round 0: Always cooperate initially to encourage a mutually beneficial equilibrium
        if (n == 0) {
            return 0; // 0 represents cooperation
        }

        // Analyze the last 5 rounds to evaluate current opponent hostility
        int window = 5;
        double opp1DefectRate = getRecentDefectionRate(n, oppHistory1, window);
        double opp2DefectRate = getRecentDefectionRate(n, oppHistory2, window);

        // Defensive Mechanism: If either opponent has a defection rate > 40% recently, defect
        if (opp1DefectRate > 0.4 || opp2DefectRate > 0.4) {
            return 1; 
        }

        // Immediate Retaliation: If both opponents defected on the exact previous turn, strike back
        if (oppHistory1[n - 1] == 1 && oppHistory2[n - 1] == 1) {
            return 1;
        }

        // Default: Forgive past distant transgressions and cooperate
        return 0; 
    }
}