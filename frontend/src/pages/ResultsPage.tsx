import { useCallback } from 'react';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { ArrowLeft, Copy } from 'lucide-react';
import type { ProcessResponse } from '../types';

interface Props {
  data: ProcessResponse | null;
  onBack: () => void;
}

export default function ResultsPage({ data, onBack }: Props) {

  const copyToClipboard = useCallback((text: string, filename: string) => {
    navigator.clipboard.writeText(text);
    // If you have a toast library installed: toast.success(`Summary for ${filename} copied`)
  }, []);

  if (!data) {
    return <div className="p-8 text-center text-gray-500">No results available</div>;
  }

  return (
    <div className="max-w-6xl mx-auto py-8 px-6">
      <div className="flex items-center gap-4 mb-8">
        <Button variant="outline" onClick={onBack}>
          <ArrowLeft className="mr-2 h-4 w-4" />
          Back to Upload
        </Button>
        <h1 className="text-3xl font-bold text-gray-900 dark:text-white">
          Processing Results
        </h1>
      </div>

      <div className="mb-6 text-lg text-gray-600 dark:text-gray-400">
        Processed {data.processed_files} file(s) • Hybrid TextRank + BART
      </div>

      <div className="space-y-10">
        {data.results.map((result) => (
          <Card key={result.filename} className="overflow-hidden">
            <CardHeader className="bg-teal-50 dark:bg-teal-950 border-b">
              <CardTitle className="flex justify-between items-center">
                <span>{result.filename}</span>
                {result.error && <span className="text-red-500 text-sm">Error</span>}
              </CardTitle>
            </CardHeader>

            <CardContent className="p-0">
              {!result.error && result.extractive && result.abstractive_summary ? (
                <Tabs defaultValue="extractive" className="w-full">
                  <TabsList className="w-full grid grid-cols-2 rounded-none">
                    <TabsTrigger value="extractive">Extractive (TextRank)</TabsTrigger>
                    <TabsTrigger value="abstractive">Abstractive Summary</TabsTrigger>
                  </TabsList>

                  {/* Extractive Tab */}
                  <TabsContent value="extractive" className="p-6">
                    <h3 className="font-semibold mb-4 text-lg">Ranked Key Sentences</h3>
                    <div className="space-y-5">
                      {result.extractive.key_sentences.map((sent, i) => (
                        <div key={i} className="flex gap-5 p-5 border rounded-xl">
                          <div className="flex-shrink-0 w-9 h-9 rounded-full bg-teal-100 dark:bg-teal-900 flex items-center justify-center text-teal-700 dark:text-teal-300 font-mono font-bold">
                            {sent.rank}
                          </div>
                          <div className="flex-1">
                            <p className="leading-relaxed text-gray-700 dark:text-gray-300">
                              {sent.sentence}
                            </p>
                            <div className="mt-3 flex gap-6 text-sm">
                              <span className="font-medium text-teal-600">
                                Score: {sent.score}
                              </span>
                              <span className="text-gray-500">
                                Position: {sent.original_position + 1}
                              </span>
                            </div>
                          </div>
                        </div>
                      ))}
                    </div>
                  </TabsContent>

                  {/* Abstractive Tab */}
                  <TabsContent value="abstractive" className="p-6">
                    <div className="flex justify-between items-start mb-4">
                      <h3 className="font-semibold text-lg">Abstractive Summary</h3>
                      <Button 
                        variant="outline" 
                        size="sm"
                        onClick={() => copyToClipboard(result.abstractive_summary, result.filename)}
                      >
                        <Copy className="mr-2 h-4 w-4" />
                        Copy Summary
                      </Button>
                    </div>
                    <div className="p-6 bg-gray-50 dark:bg-gray-900 rounded-2xl border leading-relaxed text-[15px] text-gray-700 dark:text-gray-200">
                      {result.abstractive_summary}
                    </div>
                  </TabsContent>
                </Tabs>
              ) : (
                <div className="p-8 text-center text-red-500">
                  Failed to process this file: {result.error}
                </div>
              )}
            </CardContent>
          </Card>
        ))}
      </div>
    </div>
  );
}