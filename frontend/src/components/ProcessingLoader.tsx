export default function ProcessingLoader({ message = "Processing your documents..." }: { message?: string }) {
  return (
    <div className="flex flex-col items-center justify-center py-20">
      <div className="animate-spin inline-block w-8 h-8 sm:w-12 sm:h-12 border-4 border-teal-500 border-t-transparent rounded-full"></div>
      <p className="mt-4 text-[0.85em] sm:text-[0.95em] text-gray-400">{message}</p>
    </div>
  );
}
