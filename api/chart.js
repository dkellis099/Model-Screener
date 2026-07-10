export default async function handler(req, res) {
    const { symbol } = req.query;
    const r = await fetch(
      `https://financialmodelingprep.com/api/v3/historical-price-full/${symbol}?apikey=${process.env.FMP_API_KEY}`
    );
    const data = await r.json();
    res.status(200).json(data);
  }