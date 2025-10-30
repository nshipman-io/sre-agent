import { useState } from 'react';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { Sidebar } from './components/Sidebar';
import { Chat } from './components/Chat';

const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      refetchOnWindowFocus: false,
      retry: 1,
    },
  },
});

function App() {
  const [selectedNamespace, setSelectedNamespace] = useState('default');

  return (
    <QueryClientProvider client={queryClient}>
      <div className="flex h-screen">
        <Sidebar
          selectedNamespace={selectedNamespace}
          onNamespaceChange={setSelectedNamespace}
        />
        <Chat namespace={selectedNamespace} />
      </div>
    </QueryClientProvider>
  );
}

export default App;
