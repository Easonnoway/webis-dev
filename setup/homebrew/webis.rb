class Webis < Formula
  desc "AI-Powered Knowledge Pipeline"
  homepage "https://webis.dev"
  url "https://github.com/webis-ai/webis/archive/v2.0.0.tar.gz"
  sha256 "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855"
  license "MIT"

  depends_on "python@3.10"

  def install
    virtualenv_install_with_resources
  end

  test do
    system "#{bin}/webis", "--version"
  end
end
