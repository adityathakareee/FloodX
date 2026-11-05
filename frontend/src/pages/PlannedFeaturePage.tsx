import React from 'react';
import { Link, useLocation } from 'react-router-dom';
import {
  Activity,
  AlertTriangle,
  Users,
  Navigation,
  Home,
  Truck,
  Brain,
  Sliders,
  FileText,
  Settings as SettingsIcon,
  Clock,
  ArrowLeft,
  Shield,
  Layers,
} from 'lucide-react';
import { Card } from '../components/common/Card';
import { Badge } from '../components/common/Badge';

interface ModuleConfig {
  title: string;
  tagline: string;
  phase: number;
  phaseTitle: string;
  icon: React.ComponentType<{ className?: string }>;
  overview: string;
  deliverables: string[];
  techStack: string[];
}

const MODULE_CONFIGS: Record<string, ModuleConfig> = {
  '/monitoring': {
    title: 'Live Telemetry & Sensor Monitoring',
    tagline: 'Multi-source real-time river stage & precipitation ingestion',
    phase: 1,
    phaseTitle: 'Phase 1: Real-Time Data Integration & GIS Intelligence',
    icon: Activity,
    overview:
      'Ingests live river stage levels from CWC gauges (Holkar Bridge, Deccan Gymkhana), IMD precipitation stations, and Khadakwasla Dam spillway discharge telemetry.',
    deliverables: [
      'IMD & CWC automated API connector adapters',
      'Khadakwasla Dam discharge rate polling (cusecs)',
      'Water stage threshold alerts (Normal, Warning, Danger levels)',
      'TimescaleDB / PostGIS timeseries telemetry logging',
    ],
    techStack: ['Python', 'FastAPI', 'Celery/APScheduler', 'PostGIS', 'WebSockets'],
  },
  '/risk': {
    title: 'AI/ML Flood-Risk Prediction',
    tagline: 'Hydrological runoff modeling & inundation extent classification',
    phase: 2,
    phaseTitle: 'Phase 2: AI/ML Flood Prediction & Vulnerability Analysis',
    icon: AlertTriangle,
    overview:
      'Predicts floodwater crest arrival times, peak inundation depth, and geographical flood footprints across the Pune metropolitan river corridor.',
    deliverables: [
      'Precipitation-to-runoff rainfall transformation model',
      'Flood hazard depth regression algorithms',
      'Dynamic wave propagation speed estimation across river reaches',
      'Time-to-impact calculation for low-lying settlements',
    ],
    techStack: ['Python', 'Scikit-learn', 'XGBoost', 'PyTorch/NumPy', 'FastAPI'],
  },
  '/vulnerability': {
    title: 'Vulnerability & Population Exposure',
    tagline: 'Demographic exposure mapping & socio-economic risk profiling',
    phase: 2,
    phaseTitle: 'Phase 2: AI/ML Flood Prediction & Vulnerability Analysis',
    icon: Users,
    overview:
      'Overlays hydrological flood risk on PMC/PCMC municipal ward demographic boundaries to quantify exposed vulnerable populations (elderly, children, informal settlements) and critical infrastructure.',
    deliverables: [
      'Ward-level demographic exposure index calculation',
      'Critical infrastructure overlay (hospitals, substations, bridges)',
      'Slum cluster vulnerability risk scoring along riverbanks',
      'Automated ward risk prioritisation matrix',
    ],
    techStack: ['GeoPandas', 'PostGIS', 'Shapely', 'FastAPI'],
  },
  '/evacuation': {
    title: 'Dynamic Safe Evacuation Routing',
    tagline: 'Topography-aware pathfinding avoiding inundated road corridors',
    phase: 3,
    phaseTitle: 'Phase 3: Dynamic Evacuation & Safe Routing',
    icon: Navigation,
    overview:
      'Generates safe, unobstructed evacuation routes that actively avoid inundated road links, submerged river bridges (e.g. Holkar Bridge, Sangam Bridge), and traffic bottlenecks.',
    deliverables: [
      'Pune road network graph integration with pgRouting',
      'Dynamic edge cost updates based on simulated water depth',
      'Submerged bridge avoidance algorithm',
      'Turn-by-turn safe route endpoints for mobile citizen app',
    ],
    techStack: ['pgRouting', 'PostGIS', 'NetworkX', 'OpenStreetMap'],
  },
  '/shelters': {
    title: 'Shelter Identification & Capacity Management',
    tagline: 'High-ground shelter registry with real-time occupancy tracking',
    phase: 3,
    phaseTitle: 'Phase 3: Dynamic Evacuation & Safe Routing',
    icon: Home,
    overview:
      'Manages verified municipal shelters (schools, indoor stadiums, relief camps) located outside 100-year flood lines, tracking live capacity, bed availability, and medical supplies.',
    deliverables: [
      'Safe high-ground shelter geodatabase',
      'Real-time bed and occupancy management',
      'Ration and medical supply logistics tracking',
      'Citizen nearest available shelter locator',
    ],
    techStack: ['PostgreSQL', 'FastAPI', 'React', 'React Native'],
  },
  '/resources': {
    title: 'Emergency Resource Optimization',
    tagline: 'Constraint-based dispatch for rescue boats, ambulances & NDRF teams',
    phase: 4,
    phaseTitle: 'Phase 4: Resource Optimization & Nugen Decision Intelligence',
    icon: Truck,
    overview:
      'Calculates optimal dispatch and staging plans for rescue boats, ambulances, mobile dewatering pumps, and NDRF/SDRF deployment companies under resource constraints.',
    deliverables: [
      'Google OR-Tools vehicle routing & resource optimization',
      'NDRF team allocation based on ward vulnerability index',
      'Rescue boat staging at flood chokepoints',
      'Fuel and equipment supply chain routing',
    ],
    techStack: ['Google OR-Tools', 'Python', 'FastAPI'],
  },
  '/decision': {
    title: 'Nugen Aligned Decision Intelligence',
    tagline: 'Explainable AI operational guidance compliant with NDMA SOPs',
    phase: 4,
    phaseTitle: 'Phase 4: Resource Optimization & Nugen Decision Intelligence',
    icon: Brain,
    overview:
      'Translates complex multi-sensor hydrological data and spatial predictions into natural language command briefings and actionable disaster recommendations aligned with National Disaster Management Authority (NDMA) Standard Operating Procedures.',
    deliverables: [
      'Nugen LLM decision intelligence engine integration',
      'NDMA SOP compliance verification for suggested actions',
      'Command briefing generation for Municipal Commissioners',
      'Plain-language citizen alert message synthesis',
    ],
    techStack: ['Nugen API', 'Python', 'FastAPI'],
  },
  '/scenarios': {
    title: 'Dam Release What-If Simulator',
    tagline: 'Interactive discharge simulation & downstream footprint projection',
    phase: 4,
    phaseTitle: 'Phase 4: Resource Optimization & Nugen Decision Intelligence',
    icon: Sliders,
    overview:
      'Enables disaster management authorities to simulate varying dam release volumes from Khadakwasla Dam (e.g., 25k, 50k, 75k, 100k cusecs) to preview downstream inundation extent hours before opening gates.',
    deliverables: [
      'Multi-tier dam discharge scenario simulator',
      'Downstream inundation area projection',
      'Time-to-crest calculation per river reach',
      'Pre-emptive evacuation window recommendations',
    ],
    techStack: ['Hydrodynamic Simulation', 'PostGIS', 'React Interactive Sliders'],
  },
  '/reports': {
    title: 'Municipal Incident Situation Reports',
    tagline: 'Formal post-event documentation & audit logs',
    phase: 5,
    phaseTitle: 'Phase 5: Complete Integration, Mobile App & Deployment',
    icon: FileText,
    overview:
      'Generates verifiable PDF incident logs, damage estimations, and post-flood audit reports for the State Disaster Management Authority (SDMA).',
    deliverables: [
      'Automated situation report (SITREP) PDF generator',
      'Disaster timeline audit logs',
      'Damage assessment survey aggregator',
    ],
    techStack: ['ReportLab / WeasyPrint', 'FastAPI'],
  },
  '/settings': {
    title: 'Platform Configuration & System Settings',
    tagline: 'API keys, pilot basin parameters, and notification channels',
    phase: 0,
    phaseTitle: 'Phase 0: Project Foundation & System Architecture',
    icon: SettingsIcon,
    overview:
      'Manage environment settings, API connectivity endpoints, telemetry polling frequencies, and access control credentials.',
    deliverables: [
      'Backend REST API endpoint configuration',
      'Database connection URL management',
      'Pilot region bounding box settings',
      'Log level and debug modes',
    ],
    techStack: ['FastAPI Settings', 'Vite Env', 'React'],
  },
};

export const PlannedFeaturePage: React.FC = () => {
  const location = useLocation();
  const config =
    MODULE_CONFIGS[location.pathname] || {
      title: 'Planned Platform Subsystem',
      tagline: 'Architectural specification for upcoming release',
      phase: 1,
      phaseTitle: 'Phase 1: Real-Time Data Integration',
      icon: Clock,
      overview: 'This module is scheduled for future release in the FLOOD-X development roadmap.',
      deliverables: ['Scheduled development milestone'],
      techStack: ['FastAPI', 'React', 'PostGIS'],
    };

  const Icon = config.icon;

  return (
    <div className="max-w-5xl mx-auto space-y-6 pb-12">
      {/* Back button */}
      <div>
        <Link
          to="/"
          className="inline-flex items-center gap-2 text-xs font-mono text-cyan-400 hover:text-cyan-300 transition-colors"
        >
          <ArrowLeft className="w-3.5 h-3.5" />
          <span>BACK TO SITUATION OVERVIEW</span>
        </Link>
      </div>

      {/* Header Card */}
      <Card className="relative overflow-hidden border-cyan-500/30">
        <div className="flex flex-col md:flex-row md:items-start justify-between gap-4">
          <div className="flex items-start gap-4">
            <div className="w-12 h-12 rounded-xl bg-cyan-500/10 border border-cyan-500/20 flex items-center justify-center text-cyan-400 shrink-0">
              <Icon className="w-6 h-6" />
            </div>
            <div>
              <div className="flex items-center gap-2 mb-1">
                <Badge variant={config.phase === 0 ? 'emerald' : 'amber'} size="sm">
                  {config.phase === 0 ? 'Foundation Active' : `Target: Phase ${config.phase}`}
                </Badge>
                <span className="text-xs font-mono text-slate-400">{config.phaseTitle}</span>
              </div>
              <h1 className="text-2xl font-bold text-white tracking-tight">{config.title}</h1>
              <p className="text-xs text-cyan-300 font-mono mt-0.5">{config.tagline}</p>
            </div>
          </div>
        </div>

        <p className="text-xs md:text-sm text-slate-300 mt-4 leading-relaxed max-w-3xl">
          {config.overview}
        </p>

        {/* Phase Boundary Notice */}
        {config.phase > 0 && (
          <div className="mt-5 p-3.5 rounded-xl bg-amber-500/10 border border-amber-500/20 flex items-start gap-3 text-xs text-amber-200">
            <Shield className="w-4 h-4 text-amber-400 shrink-0 mt-0.5" />
            <div>
              <span className="font-bold block text-amber-300">Strict Phase Boundary Notice</span>
              <span>
                This subsystem is actively scheduled for <strong>{config.phaseTitle}</strong>.
                In adherence to Phase 0 requirements, no simulated or fabricated data is displayed.
              </span>
            </div>
          </div>
        )}
      </Card>

      {/* Planned Deliverables & Tech Stack */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        <Card>
          <div className="flex items-center gap-2 mb-3 text-sm font-bold text-white uppercase tracking-wider font-mono">
            <Layers className="w-4 h-4 text-cyan-400" />
            <span>Target Deliverables</span>
          </div>
          <ul className="space-y-2 text-xs text-slate-300">
            {config.deliverables.map((item, idx) => (
              <li key={idx} className="flex items-start gap-2 bg-[#091024]/60 p-2.5 rounded-lg border border-[#1E325F]/40">
                <span className="w-1.5 h-1.5 rounded-full bg-cyan-400 mt-1.5 shrink-0" />
                <span>{item}</span>
              </li>
            ))}
          </ul>
        </Card>

        <Card>
          <div className="flex items-center gap-2 mb-3 text-sm font-bold text-white uppercase tracking-wider font-mono">
            <Clock className="w-4 h-4 text-cyan-400" />
            <span>Architecture & Technology Stack</span>
          </div>
          <div className="flex flex-wrap gap-2 mb-4">
            {config.techStack.map((tech, idx) => (
              <span
                key={idx}
                className="px-2.5 py-1 rounded-md text-xs font-mono font-medium bg-[#091024] text-cyan-300 border border-[#1E325F]"
              >
                {tech}
              </span>
            ))}
          </div>
          <p className="text-xs text-slate-400 leading-relaxed">
            The Phase 0 backend architecture (FastAPI router, SQLAlchemy ORM base, Alembic migrations)
            and frontend layouts are pre-wired to integrate this subsystem cleanly.
          </p>
        </Card>
      </div>
    </div>
  );
};

