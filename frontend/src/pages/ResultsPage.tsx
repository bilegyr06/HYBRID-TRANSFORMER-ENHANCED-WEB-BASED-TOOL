// frontend/src/pages/ResultsPage.tsx
import { useEffect, useMemo, useState } from 'react';
import { toast } from 'sonner';
import DocumentResultCard from '../components/results/DocumentResultCard';
import ResultsHeader from '../components/results/ResultsHeader';
import ResultsTopTabs from '../components/results/ResultsTopTabs';
import SaveReviewSection from '../components/results/SaveReviewSection';
import SynthesisActions from '../components/results/SynthesisActions';
import SynthesisMetricsGrid from '../components/results/SynthesisMetricsGrid';
import SynthesisSummaryCard from '../components/results/SynthesisSummaryCard';
import ThematicClusters from '../components/results/ThematicClusters';
import { analyzeResults, synthesizeMultiDocument } from '../lib/api';
import {
  buildAnalysisDocuments,
  buildExtractiveSentences,
  buildResultMetrics,
  emptyResultMetrics,
  topKSentences,
  type DocumentTab,
  type ResultMetrics,
  type RichExtractiveSentence,
  type ViewTab,
} from '../lib/results';
import type { ProcessResponse, SynthesisResult } from '../types';

interface ResultsPageProps {
  data: ProcessResponse | null;
  onBack: () => void;
  onSaveReview: () => void;
  onGoToMyReviews: () => void;
  reviewTitle: string;
  setReviewTitle: (title: string) => void;
}

export default function ResultsPage({
  data,
  onBack,
  onSaveReview,
  onGoToMyReviews,
  reviewTitle,
  setReviewTitle,
}: ResultsPageProps) {
  const [activeTab, setActiveTab] = useState<ViewTab>('results');
  const [activeDocTabs, setActiveDocTabs] = useState<Record<string, DocumentTab>>({});
  const [copiedId, setCopiedId] = useState<string | null>(null);
  const [themesData, setThemesData] = useState<Record<string, string[]>>({});
  const [loadingThemes, setLoadingThemes] = useState<Record<string, boolean>>({});
  const [metricsCache, setMetricsCache] = useState<Record<string, ResultMetrics>>({});
  const [displaySynthesis, setDisplaySynthesis] = useState<SynthesisResult | null>(data?.synthesis ?? null);
  const [baseSynthesisInput, setBaseSynthesisInput] = useState<RichExtractiveSentence[]>([]);
  const [synthesisInput, setSynthesisInput] = useState<RichExtractiveSentence[]>([]);
  const [synthesisActionBusy, setSynthesisActionBusy] = useState(false);

  useEffect(() => {
    if (!data) return;

    const initialInput = buildExtractiveSentences(data);
    setDisplaySynthesis(data.synthesis ?? null);
    setBaseSynthesisInput(initialInput);
    setSynthesisInput(initialInput);
    setMetricsCache(Object.fromEntries(data.results.map((result) => [result.filename, buildResultMetrics(result)])));

    if (data.synthesis) return;

    const documents = buildAnalysisDocuments(data);
    if (!Object.keys(documents).length) return;

    let cancelled = false;
    setLoadingThemes(Object.fromEntries(data.results.map((result) => [result.filename, true])));

    const hydrateAnalysis = async () => {
      try {
        const response = await analyzeResults({
          mode: 'overall',
          documents,
          compute_rouge: true,
          top_k: 10,
          coverage_target: 0.35,
        });

        if (cancelled) return;

        setDisplaySynthesis(response.synthesis ?? null);
        setThemesData(Object.fromEntries(response.results.map((result) => [result.filename, result.key_themes || []])));
        setMetricsCache(Object.fromEntries(response.results.map((result) => [result.filename, buildResultMetrics(result)])));
        setLoadingThemes(Object.fromEntries(response.results.map((result) => [result.filename, false])));
      } catch (error) {
        console.error('Failed to hydrate analysis:', error);
        setLoadingThemes(Object.fromEntries(data.results.map((result) => [result.filename, false])));
      }
    };

    void hydrateAnalysis();

    return () => {
      cancelled = true;
    };
  }, [data]);

  const synthesisPayload = useMemo(() => {
    if (synthesisInput.length > 0) return synthesisInput;
    return baseSynthesisInput;
  }, [baseSynthesisInput, synthesisInput]);

  if (!data) {
    return <div className="text-center py-20 text-gray-400">No results available</div>;
  }

  const copyToClipboard = async (text: string, id: string) => {
    try {
      await navigator.clipboard.writeText(text);
      setCopiedId(id);
      toast.success('Copied to clipboard!');
      setTimeout(() => setCopiedId(null), 2000);
    } catch {
      toast.error('Failed to copy to clipboard');
    }
  };

  const setActiveDocTab = (filename: string, tab: DocumentTab) => {
    setActiveDocTabs(prev => ({ ...prev, [filename]: tab }));
  };

  const hasSynthesis = Boolean(displaySynthesis?.abstractive_summary || data.overall_synthesis);
  const synthesisSummary = displaySynthesis?.abstractive_summary || data.overall_synthesis || '';

  const runSynthesisAction = async (
    action: 'regenerate' | 'export' | 'save',
    options: { regen_k?: number; export_format?: 'md' | 'docx' } = {},
  ) => {
    if (!synthesisPayload.length) {
      toast.error('No extractive sentences available for synthesis actions.');
      return;
    }

    try {
      setSynthesisActionBusy(true);
      const requestInput = action === 'regenerate'
        ? (baseSynthesisInput.length > 0 ? baseSynthesisInput : synthesisPayload)
        : synthesisPayload;

      const response = await synthesizeMultiDocument({
        extractive_sentences: requestInput,
        action,
        regen_k: options.regen_k,
        export_format: options.export_format,
        title: reviewTitle.trim() || undefined,
      });

      if (action === 'regenerate') {
        setSynthesisInput(topKSentences(requestInput, options.regen_k || 5));
        setDisplaySynthesis(response.data);
        toast.success('Synthesis regenerated.');
      } else if (action === 'export') {
        toast.success(response.message || 'Export completed.');
      } else {
        setDisplaySynthesis(response.data);
        toast.success(response.message || 'Saved to project library.');
      }
    } catch (error) {
      console.error(error);
      toast.error(`Synthesis ${action} failed.`);
    } finally {
      setSynthesisActionBusy(false);
    }
  };

  return (
    <div className="min-h-screen bg-gray-950 text-white pb-12">
      <ResultsHeader processedFiles={data.processed_files} onBack={onBack} />

      <div className="max-w-full md:max-w-6xl mx-auto px-4 sm:px-6 md:px-8">
        {hasSynthesis && (
          <ResultsTopTabs activeTab={activeTab} onTabChange={setActiveTab} />
        )}

        {activeTab === 'synthesis' && hasSynthesis && (
          <div className="space-y-6 mb-12">
            {displaySynthesis && (
              <SynthesisMetricsGrid
                synthesis={displaySynthesis}
                fallbackDocumentCount={data.results.length}
                summary={synthesisSummary}
              />
            )}

            <SynthesisSummaryCard
              synthesis={displaySynthesis}
              summary={synthesisSummary}
              documentCount={data.results.length}
              copied={copiedId === 'synthesis'}
              onCopy={() => copyToClipboard(synthesisSummary, 'synthesis')}
            />

            <ThematicClusters clusters={displaySynthesis?.key_themes_clustered} />

            <SynthesisActions
              busy={synthesisActionBusy}
              onRegenerate={() => runSynthesisAction('regenerate', { regen_k: 5 })}
              onSave={() => runSynthesisAction('save')}
              onExport={() => runSynthesisAction('export', { export_format: 'md' })}
            />
          </div>
        )}

        {activeTab === 'results' && data.results.map((result) => (
          <DocumentResultCard
            key={result.filename}
            result={result}
            activeTab={activeDocTabs[result.filename] || 'summary'}
            metrics={metricsCache[result.filename] || emptyResultMetrics}
            themes={themesData[result.filename] || []}
            isLoadingThemes={loadingThemes[result.filename] || false}
            copiedId={copiedId}
            onTabChange={setActiveDocTab}
            onCopy={copyToClipboard}
          />
        ))}
      </div>

      {!displaySynthesis && (
        <SaveReviewSection
          reviewTitle={reviewTitle}
          setReviewTitle={setReviewTitle}
          onSaveReview={onSaveReview}
          onGoToMyReviews={onGoToMyReviews}
        />
      )}
    </div>
  );
}
