export default function UploadHeader() {
  return (
    <header className="border-b border-gray-800 bg-gray-900">
      <div className="max-w-full md:max-w-6xl mx-auto px-4 sm:px-6 md:px-8 py-4 sm:py-5 md:py-6">
        <div className="flex flex-col md:flex-row md:items-center md:justify-between gap-2 md:gap-4">
          <h1 className="text-lg sm:text-xl md:text-2xl font-bold">Upload</h1>
          <p className="text-gray-400 text-xs sm:text-sm md:text-base">
            Hybrid TextRank + BART - Extract insights from research papers
          </p>
        </div>
      </div>
    </header>
  );
}
