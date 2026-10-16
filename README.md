# ZeroWaste AI 🌱
### AI-Powered Grocery Intelligence for Profitability, Waste Reduction & Sustainability

**ZeroWaste AI** is evolving into an AI-powered business intelligence platform for small Indian grocery stores (kirana shops). It aims to help shop owners reduce food waste, monitor operating expenses, understand profit and loss, track utility bills, and estimate their environmental impact—all from one dashboard.

🌐 **Live Demo:** https://zerowaste-grocery-assistant.onrender.com  
💻 **GitHub Repository:** https://github.com/rihaanps-hash/zerowaste-grocery-assistant

---

## 🎯 Problem Statement

Small grocery stores often face several connected challenges:

- Perishable products expire before they can be sold.
- Demand fluctuates with customer behaviour, seasons, and festivals.
- Electricity and water bills increase operating costs.
- Shop owners may not have a clear, consolidated view of profit and loss.
- Food waste and energy consumption contribute to environmental emissions.
- Managing bills, inventory, expenses, and sustainability separately takes time.

ZeroWaste AI aims to bring these problems together in one simple, practical platform.

## 🚀 Project Vision

Transform ZeroWaste from a food-waste assistant into a **smart sustainability and profitability assistant for kirana shops**.

The system will connect inventory, sales, expenses, utility consumption, and sustainability estimates to help shop owners make better business decisions.

## ✨ Features

### 1. 🥬 AI-Powered Perishable Inventory Management

- Track grocery inventory and product expiry dates.
- Identify stock at risk of expiring.
- Forecast product demand using available sales history.
- Recommend stock rotation, discounts, and restocking actions.
- Help shop owners identify products likely to become waste.

### 2. 📈 Demand Forecasting

- Estimate future demand from historical sales data.
- Explore seasonal and festival-related demand patterns.
- Identify potential overstocking and understocking.
- Generate recommendations to improve inventory decisions.

Forecasts will be estimates and will depend on the quality and availability of sales data.

### 3. ⚡ Electricity Bill & Consumption Tracking

- Record monthly electricity bills.
- Track electricity consumption in kWh when available.
- Compare bills and consumption across months.
- Estimate electricity-related carbon emissions using a documented emissions factor.
- Suggest practical ways to reduce energy consumption and operating costs.

### 4. 💧 Water Bill & Consumption Tracking

- Record monthly water bills and due dates.
- Track water usage in litres or kilolitres when available.
- Compare water consumption across billing periods.
- Identify unusual increases in usage.
- Estimate water-related emissions only when suitable, documented emissions factors are available.

### 5. 💳 Bill Payment Assistance

Provide a dedicated bill management section with payment options for:

- PhonePe
- Google Pay
- Supported UPI payment flows
- Electricity and water bills

Planned capabilities include:

- Bill amount and due-date tracking.
- Payment status and transaction-reference records.
- Links or supported payment flows that open the relevant payment service.
- Clear confirmation when a payment has actually been verified.

**Integration note:** Real bill fetching, biller payments, and automatic payment verification depend on supported provider and biller integrations. Until those integrations are implemented, payment links and manually recorded payment statuses must not be presented as verified payments.

### 6. 💰 Shop Profit & Loss Intelligence

Give shop owners a consolidated view of their business performance.

Track:

- Sales revenue.
- Cost of goods sold.
- Inventory losses from expired or damaged products.
- Electricity and water expenses.
- Rent, transport, and other operating expenses.
- Estimated operating profit and profit margin.

The system will distinguish actual recorded results from forecasts and potential savings. Calculations will avoid double-counting inventory losses already included in recorded costs.

### 7. 🌍 Carbon Emissions Intelligence

Estimate environmental impact across supported categories:

- Food waste and associated emissions.
- Electricity consumption and associated emissions.
- Water-related emissions where reliable factors are available.
- Potential emissions avoided in simulated waste-reduction scenarios.

Results will use documented emissions factors and be reported in **kg CO₂e** where appropriate.

The platform will distinguish emissions associated with producing wasted food from emissions associated with waste disposal. It will also distinguish estimated potential reductions from measured reductions.

### 8. 🤖 AI Recommendations

Connect business and sustainability data to produce actionable recommendations.

Examples:

- Discount products approaching expiry when appropriate.
- Improve stock rotation to reduce spoilage.
- Review unusually high electricity consumption.
- Investigate increases in water usage.
- Compare the financial and environmental outcomes of different inventory decisions.

Recommendations will explain their reasoning and use calculations based on available data rather than unsupported impact claims.

### 9. 📊 Baseline vs. AI Scenario Simulator

Compare two scenarios using the same starting inventory and demand assumptions:

- **Baseline:** Business outcomes without the proposed recommendations.
- **AI-assisted:** Projected outcomes when the recommendations are followed.

Compare estimated waste, recoverable inventory value, operating costs, profit, and supported carbon-emissions estimates.

This feature is intended to demonstrate the potential value of the recommendations—not to claim guaranteed real-world savings.

### 10. 🧾 Decision Audit Trail

Record the system's recommendations and their supporting information, including:

- The identified problem.
- The data used.
- The recommended action.
- The estimated financial impact.
- The estimated environmental impact.
- The resulting simulated outcome, when available.

This helps users understand why a recommendation was generated.

---

## 🧠 Proposed System Workflow

```text
Shop Inventory + Sales Data
            |
            v
    Demand & Expiry Analysis
            |
            v
     AI Recommendation Engine
            |
            +-------------------+
            |                   |
            v                   v
     Waste Reduction      Utility Tracking
                              |
                       Electricity + Water
            |                   |
            +---------+---------+
                      |
                      v
            Profit & Loss Engine
                      |
                      v
           Carbon Impact Calculator
                      |
                      v
       Unified Business Intelligence Dashboard
```

## 📊 Planned Dashboard

The future dashboard will bring together:

| Dashboard area | Key information |
|---|---|
| Inventory | Expiry risk, overstocking, stock recommendations |
| Business performance | Revenue, costs, estimated profit and margin |
| Utilities | Electricity and water bills and consumption |
| Payments | Due dates, payment options and payment records |
| Sustainability | Food waste, supported emissions estimates and trends |
| AI insights | Recommendations and projected financial and environmental outcomes |

## 🛠️ Technology & Architecture

The repository currently contains Python application modules, agent-related code, a data simulator, an orchestrator, an evaluator, a decision logger, templates, and a database file.

The expanded architecture will build on the existing code where practical. The exact implementation of each new feature will be documented as it is added and tested.

## 🗺️ Development Roadmap

- [x] Initial ZeroWaste Grocery Assistant prototype
- [x] Initial agent-oriented project structure
- [ ] Audit and stabilise the existing application
- [ ] Add electricity and water bill management
- [ ] Add utility consumption tracking
- [ ] Build a reliable profit-and-loss calculation engine
- [ ] Add documented carbon-emissions calculations
- [ ] Add PhonePe and Google Pay payment options
- [ ] Implement and verify supported payment integrations, where feasible
- [ ] Connect inventory recommendations to financial and environmental outcomes
- [ ] Add baseline-versus-AI simulation
- [ ] Test calculations, edge cases, and end-to-end workflows

Roadmap items are planned features and should not be considered implemented until they are built and tested.

## 🌱 Expected Impact

ZeroWaste AI aims to help small grocery stores:

- Reduce avoidable food waste.
- Make better inventory decisions.
- Understand their operating costs and profitability.
- Track electricity and water consumption.
- Identify opportunities for financial savings.
- Estimate their environmental impact using transparent calculations.

Actual savings and emissions reductions will depend on each shop's data and the actions taken.

## ⚠️ Data & Calculation Transparency

- Financial results depend on the completeness and accuracy of recorded data.
- Demand forecasts are estimates, not guarantees.
- Carbon estimates depend on the emissions factors and system boundaries used.
- Simulated outcomes are not proof of real-world impact.
- Payment status must not be labelled verified unless confirmation is available from a trusted payment source.

## 🤝 Contributing

Contributions, ideas, and feedback are welcome. Help us build practical AI tools that make small grocery businesses more efficient and sustainable.

## 📄 License

Add the project's chosen open-source license here once it has been selected.
