"use client";

import React from "react";
import dynamic from "next/dynamic";
import Navigation from "../../components/Navigation";

// IMPORT & REGISTER CHART.JS MODULES
import {
  Chart as ChartJS,
  CategoryScale,
  LinearScale,
  BarElement,
  Title,
  Tooltip,
  Legend,
} from "chart.js";

// Register components
ChartJS.register(
  CategoryScale,
  LinearScale,
  BarElement,
  Title,
  Tooltip,
  Legend
);

// Load the Bar chart dynamically to avoid SSR issues
const Bar = dynamic(() => import("react-chartjs-2").then(mod => mod.Bar), {
  ssr: false,
});

// Dummy GIS Data (static)
const gisData = {
  geocode: {
    lat: 25.123,
    lon: 91.456,
    display_name: "Shillong, Meghalaya, India",
  },
  elevation_m: 1523,
  flood_risk: "low",
  notes: ["High terrain elevation reducing flood vulnerability"],
};

// Dummy risk simulation chart data
const riskChartData = {
  labels: ["P10", "P50", "P90"],
  datasets: [
    {
      label: "Cost Overrun (%)",
      data: [5, 18, 37],
      borderWidth: 2,
      backgroundColor: "rgba(59,130,246,0.6)",
    },
  ],
};

const costOverrunData = {
  labels: ["Mean Cost", "P50", "P90"],
  datasets: [
    {
      label: "Cost (₹ Lakhs)",
      data: [112, 128, 160],
      borderWidth: 2,
      backgroundColor: "rgba(239,68,68,0.6)",
    },
  ],
};

export default function DashboardPage() {
  return (
    <div className="pt-28 px-6 md:px-14 pb-20 text-white space-y-12 min-h-screen bg-gradient-to-br from-gray-900 to-black text-white">
      <Navigation />
      {/* PAGE TITLE */}
      <h1 className="text-4xl font-bold tracking-tight">📊 DPR GIS & Risk Analytics</h1>
      <p className="text-gray-400 text-lg">
        A static advanced dashboard showcasing GIS, elevation, flood risk &
        analytic charts — without uploading a DPR.
      </p>

      {/*  METRIC CARDS */}
      <section className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-6">
        <MetricCard title="Latitude" value={gisData.geocode.lat} />
        <MetricCard title="Longitude" value={gisData.geocode.lon} />
        <MetricCard title="Elevation (m)" value={gisData.elevation_m} />
        <MetricCard title="Flood Risk" value={gisData.flood_risk.toUpperCase()} highlight />
      </section>

      {/* LOCATION CARD */}
      <section className="bg-white/5 border border-white/10 p-6 rounded-xl backdrop-blur-lg">
        <h2 className="text-2xl font-semibold mb-3">📍 Location Details</h2>
        <p className="text-gray-300">{gisData.geocode.display_name}</p>
      </section>

      {/*  MAP SECTION */}
      <section className="bg-white/5 border border-white/10 p-6 rounded-xl backdrop-blur-lg space-y-3">
        <h2 className="text-2xl font-semibold">🗺 GIS Map</h2>
        <iframe
          src={`https://www.openstreetmap.org/export/embed.html?bbox=${gisData.geocode.lon - 0.02}%2C${gisData.geocode.lat - 0.02}%2C${gisData.geocode.lon + 0.02}%2C${gisData.geocode.lat + 0.02}&layer=mapnik&marker=${gisData.geocode.lat}%2C${gisData.geocode.lon}`}
          width="100%"
          height="450"
          className="rounded-xl border border-white/20 shadow-xl"
        ></iframe>
      </section>

      {/* CHARTS GRID */}
      <section className="grid grid-cols-1 lg:grid-cols-2 gap-8">

        {/* Cost Overrun Chart */}
        <div className="bg-white/5 p-6 rounded-xl border border-white/10 backdrop-blur-lg">
          <h2 className="text-xl font-semibold mb-4">📈 Cost Overrun Analytics</h2>
          <Bar
            data={costOverrunData}
            options={{
              responsive: true,
              plugins: { legend: { labels: { color: "white" } } },
              scales: {
                x: { ticks: { color: "white" } },
                y: { ticks: { color: "white" } },
              },
            }}
          />
        </div>

        {/* Risk Chart */}
        <div className="bg-white/5 p-6 rounded-xl border border-white/10 backdrop-blur-lg">
          <h2 className="text-xl font-semibold mb-4">⚠️ Risk Distribution</h2>
          <Bar
            data={riskChartData}
            options={{
              responsive: true,
              plugins: { legend: { labels: { color: "white" } } },
              scales: {
                x: { ticks: { color: "white" } },
                y: { ticks: { color: "white" } },
              },
            }}
          />
        </div>

      </section>

      {/* NOTES */}
      <section className="bg-white/5 p-6 rounded-xl border border-white/10 backdrop-blur-lg">
        <h2 className="text-xl font-semibold mb-4">📝 Observations</h2>
        <ul className="list-disc pl-6 space-y-2 text-gray-300">
          {gisData.notes.map((n, i) => (
            <li key={i}>{n}</li>
          ))}
        </ul>
      </section>

    </div>
  );
}

/*  REUSABLE METRIC CARD */
function MetricCard({
  title,
  value,
  highlight = false,
}: {
  title: string;
  value: any;
  highlight?: boolean;
}) {
  return (
    <div
      className={`p-5 rounded-xl border shadow-xl backdrop-blur-lg
        ${highlight ? "bg-red-600/20 border-red-500/40" : "bg-white/5 border-white/10"}
      `}
    >
      <p className="text-gray-400 text-sm">{title}</p>
      <h3 className="text-2xl font-semibold mt-1">{value}</h3>
    </div>
  );
}
