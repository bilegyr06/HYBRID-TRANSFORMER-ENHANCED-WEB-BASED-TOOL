export default function UploadInfoPanel() {
  return (
    <div className="space-y-4 sm:space-y-6">
      <div className="bg-gray-900/80 border border-gray-800/90 rounded-2xl p-5 sm:p-6 md:p-7 shadow-sm">
        <h3 className="text-lg sm:text-xl font-semibold mb-3 sm:mb-4">How it works</h3>
        <ol className="space-y-3 sm:space-y-4 text-xs sm:text-sm text-gray-300">
          {[
            'Upload PDF or TXT documents about your research topic',
            'Our AI extracts key sentences using TextRank algorithm',
            'BART model generates abstractive summaries',
            'Save your review with a custom title for future reference',
          ].map((step, index) => (
            <li key={step} className="flex gap-2 sm:gap-3">
              <span className="font-bold text-teal-400 flex-shrink-0">{index + 1}</span>
              <span>{step}</span>
            </li>
          ))}
        </ol>
      </div>

      <div className="bg-gray-900/80 border border-gray-800/90 rounded-2xl p-5 sm:p-6 md:p-7 shadow-sm">
        <h3 className="text-lg sm:text-xl font-semibold mb-2 sm:mb-3">Supported Formats</h3>
        <div className="space-y-2 text-xs sm:text-sm text-gray-400">
          <p>PDF (.pdf)</p>
          <p>Plain Text (.txt)</p>
        </div>
      </div>
    </div>
  );
}
