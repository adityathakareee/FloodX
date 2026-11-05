import React from 'react';
import { BrowserRouter, Routes, Route } from 'react-router-dom';
import { AppLayout } from './components/layout/AppLayout';
import { OverviewPage } from './pages/OverviewPage';
import { DataIntelligencePage } from './pages/DataIntelligencePage';
import { FloodRiskPage } from './pages/FloodRiskPage';
import { FloodImpactPage } from './pages/FloodImpactPage';
import { RoadNetworkPage } from './pages/RoadNetworkPage';
import { CommandCenterPage } from './pages/CommandCenterPage';
import { PlannedFeaturePage } from './pages/PlannedFeaturePage';
import { NotFoundPage } from './pages/NotFoundPage';

export const App: React.FC = () => {
  return (
    <BrowserRouter>
      <Routes>
        <Route element={<AppLayout />}>
          <Route path="/" element={<OverviewPage />} />
          <Route path="/monitoring" element={<DataIntelligencePage />} />
          <Route path="/risk" element={<FloodRiskPage />} />
          <Route path="/vulnerability" element={<FloodImpactPage />} />
          <Route path="/impact" element={<FloodImpactPage />} />
          <Route path="/evacuation" element={<RoadNetworkPage />} />
          <Route path="/shelters" element={<RoadNetworkPage />} />
          <Route path="/command-center" element={<CommandCenterPage />} />
          <Route path="/resources" element={<CommandCenterPage />} />
          <Route path="/decision" element={<CommandCenterPage />} />
          <Route path="/scenarios" element={<CommandCenterPage />} />
          <Route path="/reports" element={<PlannedFeaturePage />} />
          <Route path="/settings" element={<PlannedFeaturePage />} />
          <Route path="*" element={<NotFoundPage />} />
        </Route>
      </Routes>
    </BrowserRouter>
  );
};

export default App;

