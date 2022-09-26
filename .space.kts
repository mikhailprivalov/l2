job("Fix version") {
    git {
        refSpec {
            +"release"
            +"refs/tags/*:refs/tags/*"
        }
        depth = UNLIMITED_DEPTH
    }
    
    container(displayName = "Run do release", image = "alpine") {
        shellScript {
            location = "./update-version.sh"
        }
        shellScript {
            content = """
            	git commit -a -m "Up version"
            
            	V=$(sed -n 's/^version = "\(.*\)"/\1/p' pyproject.toml)

                echo "Releasing version $V"

                git tag -a v$V -m "Release $V"
                git push origin v$V
            """
        }
    }
}