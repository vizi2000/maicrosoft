import { Routes, Route } from 'react-router-dom'
import Layout from './components/shared/Layout'

// Pages
import Dashboard from './pages/Dashboard'
import Login from './pages/Login'
import Register from './pages/Register'
import WorkflowList from './pages/WorkflowList'
import WorkflowBuilder from './pages/WorkflowBuilder'
import WorkflowBuilder from './pages/WorkflowBuilder'
import RunHistory from './pages/RunHistory'
import RunDetails from './pages/RunDetails'
import TemplateGallery from './pages/TemplateGallery'
import SecretManager from './pages/SecretManager'
import Settings from './pages/Settings'
import GitHubAnalyzer from './pages/GitHubAnalyzer'

function App() {
  return (
    <Layout>
      <Routes>
      <Route path="/" element={<Dashboard />} />
      <Route path="/login" element={<Login />} />
      <Route path="/register" element={<Register />} />
      <Route path="/workflows" element={<WorkflowList />} />
      <Route path="/workflows/new" element={<WorkflowBuilder />} />
      <Route path="/workflows/{id}" element={<WorkflowBuilder />} />
      <Route path="/runs" element={<RunHistory />} />
      <Route path="/runs/{id}" element={<RunDetails />} />
      <Route path="/templates" element={<TemplateGallery />} />
      <Route path="/secrets" element={<SecretManager />} />
      <Route path="/settings" element={<Settings />} />
      <Route path="/analyze" element={<GitHubAnalyzer />} />
      </Routes>
    </Layout>
  )
}

export default App
