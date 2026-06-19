export default function TestPage() {
  return (
    <div className="min-h-screen bg-gradient-to-br from-blue-600 to-purple-600 flex items-center justify-center p-8">
      <div className="bg-white rounded-2xl shadow-2xl p-8 max-w-md w-full">
        <h1 className="text-3xl font-bold text-gray-900 mb-4">
          Tailwind Test
        </h1>
        <p className="text-gray-600 mb-6">
          Se você está vendo este card com estilos bonitos, o Tailwind está funcionando!
        </p>
        <div className="flex gap-3">
          <button className="bg-blue-600 text-white px-4 py-2 rounded-lg hover:bg-blue-700 transition-colors">
            Botão 1
          </button>
          <button className="bg-gray-200 text-gray-800 px-4 py-2 rounded-lg hover:bg-gray-300 transition-colors">
            Botão 2
          </button>
        </div>
        <div className="mt-6 p-4 bg-gray-100 rounded-lg">
          <p className="text-sm text-gray-500">
            Este é um teste de componente com Tailwind CSS
          </p>
        </div>
      </div>
    </div>
  );
}
