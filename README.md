<H1>Gamma Exposure Visualizer</H1>
<p>This project allows users to visualize Gamma Exposure (GEX) data for different strike prices using real-time market data. It helps traders and financial analysts better understand the relationship between options pricing and the underlying asset’s price changes. The tool fetches market data, calculates GEX values, and dynamically updates charts to reflect the data.</p>

![image](https://github.com/user-attachments/assets/cc63220d-ddf9-4829-a57a-a1d5d319c1b3)

<H2>How It Works</H2>
<p>
The program fetches live data from the yfinance API and calculates Gamma Exposure (GEX) using options data for a given ticker symbol. The core calculations are handled through custom classes like GEXCalculator and the visualizations are updated in real-time using Plotly for dynamic chart rendering.
</p>

<ul>
  <li>Fetch Data: The program retrieves options data (such as spot price, volume, and open interest) for a given ticker symbol.</li>
  <li>Calculate GEX: Using the fetched data, the GEX for each strike price is computed.</li>
  <li>Visualization: The results are plotted and displayed dynamically on a dashboard.</li>
</ul>



https://github.com/user-attachments/assets/9d74b34b-85c6-470d-a5d6-003cb57a032a

<H2>Important</H2>


<H2>Limitations</H2>
<ul>
  <li>To run the code you need a api key from the MarketData App API</li>
  <li>Restricted to NYSE tickers</li>
  <li>Retrieves market data once every minute</li>
</ul>

<H2>Author</H2>
<p>Created by Gustav Lundborg</p>









