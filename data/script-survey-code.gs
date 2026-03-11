// Paste the URL of the Google Sheet where you want to save the responses.
const spreadsheetUrl = "https://docs.google.com/spreadsheets/d/112KB_dwdoZ4-s7AXxDovviIXVCJMK8f6zpHZPBfLCeQ/edit?gid=0#gid=0";

// --- THE CANONICAL COLUMN ORDER ---
// This array defines the exact order of columns in the Google Sheet.
// It must match the 'name' attribute of every input in your HTML form.
const COLUMN_ORDER = [
  "Timestamp",
  // Part 1: Professional Background
  "Role", "YearsOfExperience", "FamiliarityWithBIM", "CurrentBIMUsage", "ReasonForNoBIM",
  // Part 2A: Perceived Advantages - Communication
  "adv_centralizesInfo", "adv_improvesClarity3D", "adv_reducesMisunderstandings", "adv_facilitatesFeedback", "adv_enhancesIntegration",
  // Part 2B: Perceived Advantages - Collaboration
  "adv_multidisciplinaryCollab", "adv_streamlinesCoordination", "adv_integratedDelivery", "adv_remoteCollaboration", "adv_promotesTransparency",
  // Part 2C: Perceived Advantages - Productivity
  "adv_speedsUpPlanning", "adv_learningCurveJustified", "adv_automatesTakeoff", "adv_parametricModeling", "adv_boostsOverallEfficiency",
  // Part 2D: Perceived Advantages - Risk Mitigation
  "adv_clashDetection", "adv_reducesOnSiteErrors", "adv_minimizesAmbiguities", "adv_visualizesComplexSystems", "adv_improvesConstructability",
  // Part 2E: Perceived Advantages - Cost & Time
  "adv_lowersCosts", "adv_optimizesResourceUsage", "adv_cutsDownDelays", "adv_longTermSavings", "adv_smootherWorkflows",
  // Part 3A: Challenges - Communication
  "chal_dataExchange", "chal_disorganizedInfo", "chal_outdatedInfo", "chal_misinterpretation",
  // Part 3B: Challenges - Collaboration
  "chal_siloedWorkflows", "chal_ineffectiveCoordination", "chal_limitedInteroperability", "chal_lackOfTrust",
  // Part 3C: Challenges - Productivity
  "chal_steepLearningCurve", "chal_underutilizationOfFeatures", "chal_inadequateHardware", "chal_insufficientTraining",
  // Part 3D: Challenges - Risk Mitigation
  "chal_limitedClashKnowledge", "chal_poorRoleDefinitions", "chal_incompleteModels", "chal_noStandardizedProtocols",
  // Part 3E: Challenges - Cost & Time
  "chal_highInvestment", "chal_difficultyProvingROI", "chal_extendedTimelines", "chal_misalignmentOfCosts",
  // Part 4A: Strategies - Communication
  "strat_establishCDE", "strat_adoptIFC",
  // Part 4B: Strategies - Collaboration
  "strat_implementIPD", "strat_appointBimCoordinator",
  // Part 4C: Strategies - Productivity
  "strat_ongoingTraining", "strat_investInHardware",
  // Part 4D: Strategies - Risk Mitigation
  "strat_mandatoryClashDetection", "strat_developBEP",
  // Part 4E: Strategies - Cost & Time
  "strat_conductROIStudies", "strat_integrateCostTools",
  // Part 5: Demographic Profile
  "ProjectsInvolved", "OrganizationType", "Age", "Gender", "Location"
];


/**
 * Serves the HTML file of the questionnaire as a web app.
 */
function doGet() {
  return HtmlService.createHtmlOutputFromFile('Index')
    .setTitle("BIM Effectiveness Questionnaire")
    .setXFrameOptionsMode(HtmlService.XFrameOptionsMode.DEFAULT);
}

/**
 * Processes the form data submitted from the HTML page using a predefined column order.
 * @param {Object} formData The data object submitted from the form.
 * @returns {String} A success or failure message.
 */
function processForm(formData) {
  try {
    const sheet = SpreadsheetApp.openByUrl(spreadsheetUrl).getActiveSheet();
    
    // On the very first submission, create the header row using our defined order.
    if (sheet.getLastRow() === 0) {
      sheet.appendRow(COLUMN_ORDER);
    }

    // Create the new row by mapping over our COLUMN_ORDER array.
    // This ensures every piece of data is placed in the correct column.
    const newRow = COLUMN_ORDER.map(header => {
      if (header === "Timestamp") {
        return new Date();
      }
      
      const value = formData[header];
      
      // If the value is an array (from checkboxes), join it into a single string.
      if (Array.isArray(value)) {
        return value.join(', ');
      }
      
      // Return the value, or an empty string if it's missing (e.g., conditional fields).
      return value || "";
    });

    sheet.appendRow(newRow);

    return "Success! Your response has been recorded.";

  } catch (e) {
    Logger.log(e.message);
    return "Error: Could not process form. Details: " + e.message;
  }
}
