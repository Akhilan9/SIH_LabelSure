import React, { useState, useEffect } from 'react';
import { Sidebar } from './components/Sidebar';
import { TopNavbar } from './components/TopNavbar';
import { DashboardView } from './pages/DashboardView';
import { InspectionsView } from './pages/InspectionsView';
import { InspectionDetailView } from './pages/InspectionDetailView';
import { EvidenceView } from './pages/EvidenceView';
import { RuleLensView } from './pages/RuleLensView';
import { RuleExplorerView } from './pages/RuleExplorerView';
import { ReportsView } from './pages/ReportsView';
import { AnalyticsView } from './pages/AnalyticsView';
import { UsersView } from './pages/UsersView';
import { AuditLogsView } from './pages/AuditLogsView';
import { LoginView } from './pages/LoginView';
import { api, getCurrentUserFromStorage, removeAuthToken } from './api/client';
import { User } from './types';

export const App: React.FC = () => {
  const [user, setUser] = useState<User | null>(getCurrentUserFromStorage());
  const [currentTab, setCurrentTab] = useState<string>('dashboard');
  const [selectedInspectionId, setSelectedInspectionId] = useState<string | null>(null);
  const [showNewModal, setShowNewModal] = useState<boolean>(false);
  const [searchQuery, setSearchQuery] = useState<string>('');

  useEffect(() => {
    const token = localStorage.getItem('labelsure_token');
    if (token && !user) {
      api.getMe()
        .then(setUser)
        .catch(() => {
          removeAuthToken();
          setUser(null);
        });
    }
  }, []);

  const handleLogout = () => {
    removeAuthToken();
    setUser(null);
    setCurrentTab('dashboard');
  };

  const handleSelectInspection = (id: string) => {
    setSelectedInspectionId(id);
    setCurrentTab('inspection-detail');
  };

  if (!user) {
    return <LoginView onLoginSuccess={(loggedInUser) => setUser(loggedInUser)} />;
  }

  const getPageTitle = () => {
    switch (currentTab) {
      case 'dashboard':
        return 'Executive Compliance Dashboard';
      case 'inspections':
        return 'Packaged Commodity Inspections';
      case 'inspection-detail':
        return 'Inspection Dossier & Adjudication';
      case 'evidence':
        return 'Packaging Photographic Evidence Repository';
      case 'rulelens':
        return 'RuleLens™ Statutory Compliance Traceability';
      case 'rules':
        return 'Statutory Legal Metrology Rule Corpus';
      case 'reports':
        return 'Official Statutory Reports & Certificates';
      case 'analytics':
        return 'Legal Metrology Compliance Intelligence';
      case 'users':
        return 'Legal Metrology Personnel Directory';
      case 'audit':
        return 'Tamper-Evident Audit Ledger';
      default:
        return 'APEX LabelSure Platform';
    }
  };

  return (
    <div className="app-container">
      <Sidebar 
        currentTab={currentTab}
        setCurrentTab={(tab) => {
          setCurrentTab(tab);
          if (tab !== 'inspection-detail') setSelectedInspectionId(null);
        }}
        user={user}
        onLogout={handleLogout}
        onNewInspection={() => {
          setCurrentTab('inspections');
          setShowNewModal(true);
        }}
      />

      <div className="main-content">
        <TopNavbar 
          pageTitle={getPageTitle()}
          user={user}
          searchQuery={searchQuery}
          onSearchChange={currentTab === 'inspections' ? setSearchQuery : undefined}
        />

        {currentTab === 'dashboard' && (
          <DashboardView 
            onSelectInspection={handleSelectInspection}
            onNewInspection={() => {
              setCurrentTab('inspections');
              setShowNewModal(true);
            }}
          />
        )}

        {currentTab === 'inspections' && (
          <InspectionsView 
            onSelectInspection={handleSelectInspection}
            showNewModal={showNewModal}
            setShowNewModal={setShowNewModal}
          />
        )}

        {currentTab === 'inspection-detail' && selectedInspectionId && (
          <InspectionDetailView 
            inspectionId={selectedInspectionId}
            onBack={() => setCurrentTab('inspections')}
          />
        )}

        {currentTab === 'evidence' && (
          <EvidenceView 
            onOpenInspection={handleSelectInspection}
          />
        )}

        {currentTab === 'rulelens' && (
          <RuleLensView 
            initialInspectionId={selectedInspectionId}
            onOpenInspectionDetail={handleSelectInspection}
          />
        )}

        {currentTab === 'rules' && <RuleExplorerView />}

        {currentTab === 'reports' && (
          <ReportsView 
            onOpenInspection={handleSelectInspection}
          />
        )}

        {currentTab === 'analytics' && <AnalyticsView />}

        {currentTab === 'users' && (user.role === 'ADMIN' || user.role === 'SUPERVISOR') && (
          <UsersView currentUser={user} />
        )}

        {currentTab === 'audit' && <AuditLogsView />}
      </div>
    </div>
  );
};

export default App;
