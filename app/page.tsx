import NFZSearch from "@/components/NFZSearch";

export default function Main() {
  return (
    <div className="min-h-screen bg-gray-100 py-10">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="text-center mb-8">
          <h1 className="text-3xl font-extrabold text-gray-900 sm:text-4xl">
            NFZ Skierowanie
          </h1>
          <p className="mt-3 max-w-md mx-auto text-base text-gray-500 sm:text-lg md:mt-5 md:text-xl md:max-w-3xl">
            Wyszukaj placówki medyczne dla Twojego skierowania
          </p>
        </div>

        <NFZSearch />
      </div>
    </div>
  );
}
